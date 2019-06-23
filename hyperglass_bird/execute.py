"""
Execute the constructed command
"""
# Standard Imports
import logging
import subprocess

# Module Imports
import logzero
from logzero import logger

# Project Imports
from hyperglass_bird import configuration

# Logzero Configuration
if configuration.debug_state():
    logzero.loglevel(logging.DEBUG)
else:
    logzero.loglevel(logging.INFO)

bird_version = configuration.bird_version()
logger.debug(f"BIRD Version: {bird_version}")


def parse(raw):
    """Parses birdc output to remove first 2 lines stating birdc version & access restricted \
    messages"""
    # Convert from byte object to string object
    raw_str = str(raw, "utf-8")
    logger.debug(f"Pre-parsed output:\n{raw_str}")
    # Parse birdc ouput to remove first line containing version
    parsed = raw_str.split("\n", 2)[2:]
    logger.debug(f"Post-parsed output:\n{parsed}")
    return parsed


def execute(query):
    """Gets constructed command string and runs the command via subprocess"""
    logger.debug(f"Received query: {query}")
    query_type = query.get("query_type")
    output = None
    status = 500
    try:
        command = configuration.Command(query)
        if bird_version < 2:
            if query_type in ["bgp_route"]:
                to_run = command.birdc_1()
                logger.debug(f'Running command "{to_run}"')
                status = 200
                output = parse(subprocess.check_output(to_run))
            elif query_type in ["bgp_aspath", "bgp_community"]:
                to_run = command.birdc_1()
                logger.debug(f'Running command "{to_run}"')
                status = 200
                output4 = parse(subprocess.check_output(to_run[0]))
                output6 = parse(subprocess.check_output(to_run[1]))
                output = output4[0] + "\n" + output6[0]
        if query_type in ["ping", "traceroute"]:
            logger.debug(f'Running bash command "{command}"')
            to_run = command.is_split()
            output = subprocess.check_output(to_run)
            status = 200
    except (RuntimeError, subprocess.CalledProcessError) as error_exception:
        output = f"Error running query for {query}"
        status = 500
        logger.error(f"Error running query for {query}. Error:\n{error_exception}")
    return (output, status)
