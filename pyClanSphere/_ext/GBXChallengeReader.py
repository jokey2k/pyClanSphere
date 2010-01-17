#!/usr/bin/env python

# GBX Challenge Reader with some salt from Xymph's PHP class
# written 2009 by Markus Ullmann <mail@markus-ullmann.de>
# License: as-is
#
# ChangeLog
# ---------
# 1.0 Initial release

import struct, os
from xml.dom.minidom import parseString

racetypes = {
-1: 'unknown',
0: 'Race',
1: 'Platform',
2: 'Puzzle',
3: 'Crazy',
5: 'Stunts'
}

class GBXReadException(Exception):
    pass

class GBXWrongFileTypeException(Exception):
    pass

# our fast init confuses pylint, so
# pylint: disable-msg=W0201, R0902
class GBXChallengeReader:
    """Class to read and hold attributes of a Trackmania Challenge Gbx"""

    def __init__(self, filename):
        self.filename = filename

        # start with values set to none so scripts don't need to do hasattr()
        for var in ['uid', 'version', 'name', 'author', 'tracktype',
                    'racetype', 'envir', 'mood', 'pub', 'authortime',
                    'goldtime','silvertime','bronzetime','coppers','multilap'
                    'unknown','unknown2','authorscore','password','xmlver'
                    'exever', 'nblaps','songfile','modname','modfile',
                    'thumbnail','comment']:
            setattr(self, var, None)
        self.rawxml = ''
        self.parsedxml = ''
        self.filehandle = None

        self.getData()

        # keep nadeo-colorized name here
        self.full_name = unicode(self.name)

        import re
        regex_format = re.compile(r'\$[g|n|o|w|s|i|l|z|G|N|O|W|S|I|L|Z]')
        regex_colors = re.compile(r'\$.{3}')
        name = regex_format.sub(u'', self.name)
        name = regex_colors.sub(u'', name)
        self.name = name

    def ReadGBXString(self):
        f = self.filehandle
        (datalen,) = struct.unpack('<l', f.read(4))
        if datalen <= 0 or datalen >= 0x10000:
            raise GBXReadException('OutOfLengthScope')
        data = f.read(datalen)
        return data

    def getData(self):
        # open file
        self.filehandle = open(self.filename, mode='rb')
        f = self.filehandle

        # Start from 0 and seek for GBX intro header
        f.seek(0)
        data = f.read(5)
        if data != 'GBX' +  chr(6) + chr(0):
            raise GBXWrongFileTypeException('GBX Header missing')

        # Read GBX Type
        f.seek(4, os.SEEK_CUR)  # "BUCR" | "BUCE"
        (data,) = struct.unpack('>L', f.read(4))
        self.tracktype = '%08X' % data

        if self.tracktype not in ['00300024', '00300403']:
            raise GBXWrongFileTypeException('Not a GBX Track')

        # GBX Version: 2/3 = TM/TMPowerUp, 4 = TMO(LevelUp)/TMS/TMN, 5 = TMU/TMF
        f.seek(4, os.SEEK_CUR) # Data Block Offset
        (self.version,) = struct.unpack('<L', f.read(4))

        if self.version < 2 or self.version > 5:
            raise GBXWrongFileTypeException('Unsupported GBX Version Format')

        # get Index (marker/lengths) table
        marks = {}
        lengths = {}
        for i in range(1, self.version+1):
            (marks[i],) = struct.unpack('>L', f.read(4))
            (lengths[i],) = struct.unpack('<L', f.read(4))
        if self.version == 5:  # clear high-bits
            lengths[4] &= 0x7FFFFFFF
            lengths[5] &= 0x7FFFFFFF

        # start of Times/info block:
        # 0x25 (TM v2), 0x2D (TMPowerUp v3), 0x35 (TMO/TMS/TMN v4), 0x3D (TMU/TMF v5)
        # get count of Times/info entries (well... sorta)
        # TM v2 tracks use 3, TMPowerUp v3 tracks use 4; actual count is 2 more
        # oldest TMO/TMS tracks (exever="0.1.3.0-0.1.4.1") use 6-8, actual count always 8; no unknown2/ascore
        # older TMS tracks (exever="0.1.4.3-6") use 9; no author score
        # newer TMO/TMS tracks (exever>="0.1.4.8") and TMN/TMU/TMF tracks (exever<="2.11.4") use 10
        # TMF tracks (exever>="2.11.5") use 11; with unknown3
        entrycount = ord(f.read(1))

        f.seek(4, os.SEEK_CUR)  # Unknown1: 00 00 00 00
        (self.bronzetime,) = struct.unpack('<L', f.read(4))
        (self.silvertime,) = struct.unpack('<L', f.read(4))
        (self.goldtime,) = struct.unpack('<L', f.read(4))
        (self.authortime,) = struct.unpack('<L', f.read(4))

        if self.version >= 3: # version >= 3, exever>="0.1.3.0"
            (self.coppers,) = struct.unpack('<L', f.read(4))

        if entrycount >= 6:
            (data,) = struct.unpack('<L', f.read(4))
            self.multilap = True if data else False

            (data,) = struct.unpack('<L', f.read(4))
            if data in racetypes.keys():
                self.racetype = data
            else:
                self.racetype = -1

        if entrycount >= 9:
            (self.unknown,) = struct.unpack('<L', f.read(4))
        if entrycount >= 10:
            (self.authorscore,) = struct.unpack('<L', f.read(4))
        if entrycount >= 11:
            (self.unknown2,) = struct.unpack('<L', f.read(4))

        # start of Strings block in version 2 (0x3A, TM)
        # start of Version? block in versions >= 3
        f.seek(4, os.SEEK_CUR)

        # 00 03 00 00 (TM v2)
        # 01 03 00 00 (TMPowerUp v3; TMO v4, exever="0.1.3.3-5"; TMS v4, exever="0.1.4.0")
        # 02 03 00 00 (TMS v4, exever="0.1.4.1-6")
        # 03 03 00 00 (TMO/TMS v4, exever="0.1.4.8", rare)
        # 04 03 00 00 (TMO/TMS/TMN v4, exever>="0.1.4.8")
        # 05 03 00 00 (TMU/TMF v5)

        # start of Strings block in versions >= 3
        # 0x4A (TMPowerUp v3)
        # 0x5A (TMO/TMS v4, exever="0.1.3.3-0.1.4.1")
        # 0x5E (TMS v4, exever="0.1.4.3-6")
        # 0x62 (TMO/TMS/TMN v4, exever>="0.1.4.8")
        # 0x6A (TMU/TMF v5, exever<="2.11.4")
        # 0x6E (TMF v5, exever>="2.11.5")

        f.seek(5, os.SEEK_CUR)  # 00 and 00 00 00 80
        self.uid = self.ReadGBXString()
        f.seek(4, os.SEEK_CUR)  # 00 00 00 40
        self.envir = self.ReadGBXString()
        f.seek(4, os.SEEK_CUR)  # 00 00 00 [04|80]
        self.author = self.ReadGBXString()
        self.name = self.ReadGBXString()
        f.seek(1, os.SEEK_CUR)  # almost always 08

        if self.version >= 3:
            f.seek(4, os.SEEK_CUR)  # varies... a lot
            # password is optional, ReadGBXString might yell at us
            try:
                self.password = self.ReadGBXString()
            except GBXReadException:
                self.password = ""

        if self.version >= 4 and entrycount >= 8:  # exever>="0.1.4.1"
            f.seek(4, os.SEEK_CUR)  # 00 00 00 40
            self.mood = self.ReadGBXString()
            f.seek(4, os.SEEK_CUR)  # 02 00 00 40
            data = f.read(4)  # 03 00 00 40 if no pub, otherwise 00 00 00 40
            if data[0] != chr(3):
                self.pub = self.ReadGBXString()
            else:
                self.pub = ''

        # set pointer to start of next block based on actual offsets
        lens = 0
        for i in range(1, self.version+1):
            lens += 8
            if i <= 3:
                lens += lengths[i]
        f.seek(0x15 + lens, os.SEEK_SET)

        # get optional XML block & wrap lines for readability
        if self.version >= 4:
            self.rawxml = self.ReadGBXString()
            self.rawxml = self.rawxml.replace("><", ">\n<")

        # get optional Thumbnail/Comments block
        if self.version >= 5:
            f.seek(4, os.SEEK_CUR)  # 01 00 00 00
            (data,) = struct.unpack('<L', f.read(4))
            f.seek(15, os.SEEK_CUR)  # '<Thumbnail.jpg>'

            # check for thumbnail
            if data > 0 and data < 0x10000:
                # extract and return thumbnail image
                data = f.read(data)


            f.seek(0x10, os.SEEK_CUR)  # '</Thumbnail.jpg>'
            f.seek(10, os.SEEK_CUR)  # '<Comments>'
            try:
                self.comment = self.ReadGBXString()
            except GBXReadException:
                self.comment = ""
            f.seek(11, os.SEEK_CUR)  # '</Comments>'

        f.close()
        # to make this pickle-able, deref file object (safe as closed before)
        self.filehandle = None

        # convert password to hex format
        if self.password:
            data = self.password
            self.password = ""
            for i in range(3, len(data)):  # skip 3 bogus chars
                self.password += '%02X' % ord(data[i])

        if self.rawxml:
            self.parsedxml = parseString(self.rawxml)

        # extract some minor details from xml if available
        myxml = self.parsedxml
        if myxml.documentElement.tagName == "header":
            # if we actually have a header (yes there are broken tracks out there)
            self.exever = myxml.documentElement.getAttribute('exever')
            self.exever = myxml.documentElement.getAttribute('version')
            descs = myxml.documentElement.getElementsByTagName('desc')[0]
            self.nblabs = descs.getAttribute('nblabs')
            if descs.hasAttribute('mod'):
                self.modname = descs.getAttribute('mod')
            else:
                self.modname = ''
            ident = myxml.documentElement.getElementsByTagName('ident')[0]
            self.author = ident.getAttribute('author')

            # skim through <deps> for songfile and modfile
            deps = myxml.documentElement.getElementsByTagName('deps')[0]
            for dep in deps.getElementsByTagName('dep'):
                filename = dep.getAttribute('file')
                if filename.find('\\Mod\\') > 0:
                    self.modfile = filename.split('\\Mod\\', 1)[1]
                elif filename.find('ChallengeMusics\\') > 0:
                    self.songfile = filename.split('ChallengeMusics\\', 1)[1]
