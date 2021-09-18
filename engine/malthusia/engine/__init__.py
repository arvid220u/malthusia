import logging
import os
import sys

from .game import Game, BasicViewer, GameConstants, RobotType
from .container import CodeContainer

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOGLEVEL", logging.WARNING))
ch = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setLevel(level=logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)
