# DuKRIF - The Duduf Krita Framework
# A Python framework used in the developement of Krita Plugins
# Copyright (c) 2020 - Nicolas Dufresne, Rainbox Laboratory
# This script is licensed under the GNU General Public License v3
# https://rainboxlab.org
#
# This file is part of DuKRIF.
#   DuKRIF is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    DuKRIF is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with DuKRIF. If not, see <http://www.gnu.org/licenses/>.

import time
import krita # pylint: disable=import-error
from PyQt5.QtCore import (Qt, QRect) # pylint: disable=no-name-in-module # pylint: disable=import-error

class DuKRIF_info():
    """This class contains useful information about DuKRIF"""

    def __init__(self):
        self.version = "0.0.2"
        self.about = """DuKRIF - The Duduf Krita Framework
            A Python framework used in the developement of Krita Plugins"""
        self.license = "GNU-GPL v3"

class DuKRIF_utils():
    """Utilitaries"""

    @staticmethod
    def intToStr(i, numDigits = 5):
        """Converts an integer to a string, prepending some 0 to get a certain number of digits"""
        s = str(i)
        while len(s) < numDigits:
            s = "0" + s
        return s

class DuKRIF_animation():
    """Methods to manage animations"""

    @staticmethod
    def setCurrentFrame(document, frameNumber):
        """Sets the current frame in the document and waits for the image to be cached."""
        document.setCurrentTime(frameNumber)
        document.refreshProjection()

    @staticmethod
    def hasKeyframeAtTime(parentNode, frameNumber, visibleNodesOnly=True ):
        """Checks if the node or one of its children has a keyframe at the given frame number"""

        if not parentNode.visible():
            return False

        if parentNode.hasKeyframeAtTime(frameNumber):
            return True

        for node in parentNode.childNodes():
            if DuKRIF_animation.hasKeyframeAtTime(node, frameNumber):
                return True

        return False

class DuKRIF_nodes():
    """Methods for layers"""

    @staticmethod
    def flattenNode(document, node, nodeIndex, parentNode):
        # create a layer right under
        mergeNode = document.createNode(node.name(), 'paintlayer')
        if nodeIndex > 0:
            aboveNode = parentNode.childNodes()[nodeIndex-1]
        else:
            aboveNode = None
        parentNode.addChildNode(mergeNode, aboveNode)
        node.mergeDown()
        return parentNode.childNodes()[nodeIndex]

    @staticmethod
    def disableIgnoreNodes(parentNode, disable=True):
        """Disables all nodes containing '_ignore_' in their name."""
        for node in parentNode.childNodes():
            if node.visible():
                if '_ignore_' in node.name():
                    node.setVisible(not disable)

                if node.type() == 'grouplayer':
                    DuKRIF_nodes.disableIgnoreNodes(node)

class DuKRIF_json():
    """Methods used to export and manage JSON files"""

    @staticmethod
    def getDocInfo(document):
        """Creates a new document info."""
        docInfo = {}
        docInfo['name'] = document.name()
        docInfo['frameRate'] = document.framesPerSecond()
        docInfo['width'] = document.width()
        docInfo['height'] = document.height()
        docInfo['startTime'] = document.fullClipRangeStartTime()
        docInfo['endTime'] = document.fullClipRangeEndTime()
        docInfo['colorDepth'] = document.colorDepth()
        bgColor = document.backgroundColor()
        docInfo['backgroundColor'] = [ bgColor.redF(), bgColor.greenF(), bgColor.blueF(), bgColor.alphaF() ]
        docInfo['layers'] = []
        docInfo['originApp'] = 'Krita'
        docInfo['originAppVersion'] = krita.Krita.instance().version()
        return docInfo

    @staticmethod
    def createNodeInfo(name, nodeType = 'paintlayer'):
        """Creates a new default node info of a given type with a given name."""
        nodeInfo = {}
        nodeInfo['name'] = name
        nodeInfo['frames'] = []
        nodeInfo['childLayers'] = []
        nodeInfo['type'] = nodeType
        nodeInfo['fileType'] = ""
        nodeInfo['blendingMode'] = 'normal'
        nodeInfo['animated'] = False
        nodeInfo['position'] = [ 0, 0 ]
        nodeInfo['width'] = 0
        nodeInfo['height'] = 0
        nodeInfo['label'] = -1
        nodeInfo['opacity'] = 1.0
        nodeInfo['visible'] = True
        nodeInfo['reference'] = False
        nodeInfo['passThrough'] = False
        nodeInfo['inheritAlpha'] = False
        return nodeInfo

    @staticmethod
    def getNodeInfo(document, node, useDocumentSize = False):
        """Constructs a new node info based on a given node"""
        nodeInfo = {}
        nodeInfo['name'] = node.name().strip()
        nodeInfo['frames'] = []
        nodeInfo['childLayers'] = []
        nodeInfo['type'] = node.type()
        nodeInfo['fileType'] = ""
        nodeInfo['blendingMode'] = node.blendingMode()
        nodeInfo['animated'] = node.animated()
        if useDocumentSize or node.animated():
            nodeInfo['position'] = [ document.width() / 2, document.height() / 2 ]
            nodeInfo['width'] = document.width()
            nodeInfo['height'] = document.height()
        else:
            nodeInfo['position'] = [ node.bounds().center().x(), node.bounds().center().y() ]
            nodeInfo['width'] = node.bounds().width()
            nodeInfo['height'] = node.bounds().height()
        nodeInfo['label'] = node.colorLabel()
        nodeInfo['opacity'] = node.opacity() / 255.0
        nodeInfo['visible'] = node.visible()
        nodeInfo['passThrough'] = False
        nodeInfo['reference'] = False
        nodeInfo['inheritAlpha'] = node.inheritAlpha()
        if node.type() == 'grouplayer':
            nodeInfo['passThrough'] = node.passThroughMode()
            nodeInfo['width'] = document.width()
            nodeInfo['height'] = document.height()
            nodeInfo['position'] = [ document.width() / 2, document.height() / 2 ]

        return nodeInfo

    @staticmethod
    def createKeyframeInfo(name, fileName, frameNumber):
        """Creates a new default keyframe info."""
        frameInfo = {}
        frameInfo['name'] = name
        frameInfo['fileName'] = fileName
        frameInfo['frameNumber'] = frameNumber
        frameInfo['opacity'] = 1.0
        frameInfo['position'] = [0,0]
        frameInfo['width'] = 0
        frameInfo['height'] = 0
        frameInfo['duration'] = 1

        return frameInfo

    @staticmethod
    def getKeyframeInfo(document, node, frameNumber, useDocumentSize = False):
        """Constructs a new keyframe info based on a given node at a given frame"""
        DuKRIF_animation.setCurrentFrame(document, frameNumber)

        frameInfo = {}
        frameInfo['name'] = '{0}_{1}'.format( node.name(), DuKRIF_utils.intToStr(frameNumber))
        frameInfo['fileName'] = ''
        frameInfo['frameNumber'] = frameNumber
        frameInfo['opacity'] = node.opacity() / 255.0
        if useDocumentSize:
            frameInfo['position'] = [ document.width() / 2, document.height() / 2 ]
            frameInfo['width'] = document.width()
            frameInfo['height'] = document.height()
        else:
            frameInfo['position'] = [ node.bounds().center().x(), node.bounds().center().y() ]
            frameInfo['width'] = node.bounds().width()
            frameInfo['height'] = node.bounds().height()
        frameInfo['duration'] = 1

        return frameInfo

class DuKRIF_io():
    """Methods to import and export images and other files from Krita"""

    @staticmethod
    def exportDocument(document, fileName, timeOut=10000):
        """Attempts to export the document for timeOut milliseconds"""

        succeed = False

        currentTime = 0
        while currentTime < timeOut:
            succeed = document.exportImage(fileName, krita.InfoObject())
            if succeed:
                break
            time.sleep(0.5)
            currentTime = currentTime + 500

        return succeed