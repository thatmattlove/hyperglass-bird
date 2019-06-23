"""
Exports constructed commands and API variables from configuration file based \
on input query
"""
# Standard Imports
import os
import re
import logging

# Module Imports
import toml
import logzero
from logzero import logger

# Project Directories
this_directory = os.path.dirname(os.path.abspath(__file__))

# TOML Imports
conf = toml.load(os.path.join(this_directory, "configuration.toml"))


def debug_state():
    """Returns string for logzero log level"""
    state = conf.get("debug", False)
    return state


# Logzero Configuration
if debug_state():
    logzero.loglevel(logging.DEBUG)
else:
    logzero.loglevel(logging.INFO)


def api():
    """Imports & exports configured API parameters from configuration file"""
    api_dict = {
        "listen_addr": conf["api"].get("listen_addr", "*"),
        "port": conf["api"].get("port", 8080),
        "key": conf["api"].get("key", 0),
    }
    return api_dict


def bird_version():
    """Get BIRD version from command line, convert version to float for comparision"""
    import subprocess
    from math import fsum

    # Get BIRD version, convert output to UTF-8 string
    ver_string = str(
        subprocess.check_output(["bird", "--version"], stderr=subprocess.STDOUT), "utf8"
    )
    # Extract numbers from string as list of numbers
    verlist_string = re.findall(r"\d+", ver_string)
    # Convert last 2 numbers in list to decimals
    verlist_string_dec = [
        verlist_string[0],
        "." + verlist_string[1],
        "." + verlist_string[2],
    ]
    # Convert number strings to floats, add together to produce whole number as version number
    version_sum = fsum([float(number) for number in verlist_string_dec])
    return version_sum


class BirdConvert:
    """Converts traditional/standard commands to BIRD formatted commands"""

    def __init__(self, target):
        self.target = target

    def bgp_aspath(self):
        """Takes traditional AS_PATH regexp pattern and converts it to an accpetable birdc format"""
        _open = r"[= "
        _close = r" =]"
        # Strip out regex characters
        stripped = re.sub(r"[\^\$\(\)\.\+]", "", self.target)
        # Replace regex _ with wildcard *
        replaced = re.sub(r"\_", r"*", stripped)
        # Remove extra * as they are not needed with wildcards
        replaced_dedup = re.sub(r"\*+", r"*", replaced)
        # Pad ASNs & wildcard operators with whitespaces
        for sub in ((r"(\d+)", r" \1 "), (r"(\*)", r" \1 ")):
            subbed = re.sub(*sub, replaced_dedup)
        # Construct bgp_path pattern for birdc
        pattern = f"{_open}{subbed}{_close}"
        # Remove extra whitespaces from constructed pattern
        pattern_dedup = re.sub(r"\s+", " ", pattern)
        return pattern_dedup

    def bgp_community(self):
        """Takes traditional BGP Community format and converts it to an acceptable birdc format"""
        # Replace : with ,
        subbed = re.sub(r"\:", r",", self.target)
        # Wrap in parentheses
        pattern = f"({subbed})"
        return pattern


class Command:
    """Imports & exports configured command syntax from configuration file"""

    def __init__(self, query):
        self.query_type = query.get("query_type")
        self.afi = query.get("afi")
        self.source = query.get("source")
        self.target = query.get("target", 0)
        logger.debug(
            f"""Command class initialized with paramaters:\nQuery Type: {self.query_type}\nAFI: \
            {self.afi}\nSource: {self.source}\nTarget: {self.target}"""
        )

    def is_split(self):
        """Returns bash command as a list of arguments"""
        command_string = (
            conf["commands"][self.afi]
            .get(self.query_type)
            .format(source=self.source, target=self.target)
        )
        command_split = command_string.split(" ")
        logger.debug(f"Constructed bash command as list: {command_split}")
        return command_split

    def birdc_1(self):
        """Returns bash command as a list of arguments, with the birdc commands as separate list \
        elements"""
        birdc4_pre = ["birdc", "-r"]
        birdc6_pre = ["birdc6", "-r"]
        to_run = None
        if self.afi == "dual":
            fmt_target = getattr(BirdConvert(self.target), self.query_type)()
            cmd4 = birdc4_pre + [
                conf["commands"]["1"].get(self.query_type).format(target=fmt_target)
            ]
            cmd6 = birdc6_pre + [
                conf["commands"]["1"].get(self.query_type).format(target=fmt_target)
            ]
            to_run = (cmd4, cmd6)
        if self.afi == "ipv4":
            to_run = birdc4_pre + [
                conf["commands"]["1"].get(self.query_type).format(target=self.target)
            ]
        if self.afi == "ipv6":
            to_run = birdc6_pre + [
                conf["commands"]["1"].get(self.query_type).format(target=self.target)
            ]
        logger.debug(f"Constructed Command: {to_run}")
        if not to_run:
            raise RuntimeError("Error constructing birdc commands")
        return to_run
