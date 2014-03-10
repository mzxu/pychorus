'''
Created on Mar 24, 2012

@author: mxu
'''
import math
import subprocess
from PIL import Image
import Utils
import  ChorusGlobals
import os
import Levenshtein

class metrictype:
    AE = 'AE'    #absolute error count, number of different pixels (-fuzz effected)
    FUZZ = 'FUZZ'   #mean color distance
    MAE = 'MAE'   #mean absolute error (normalized), average channel error distance
    MEPP = 'MEPP'  #mean error per pixel (normalized mean error, normalized peak error)
    MSE = 'MSE'   #mean error squared, average of the channel error squared
    NCC = 'NCC'   #normalized cross correlation
    PAE = 'PAE'   #peak absolute (normalize peak absolute)
    PSNR = 'PSNR'  #peak signal to noise ratio
    RMSE = 'RMSE'  #root mean squared (normalized root mean squared)

class BWImageCompare(object):
    """Compares two images (b/w)."""

    _pixel = 255
    _colour = False

    def __init__(self, imga, imgb, maxsize=64):
        """Save a copy of the image objects."""

        sizea, sizeb = imga.size, imgb.size

        newx = min(sizea[0], sizeb[0], maxsize)
        newy = min(sizea[1], sizeb[1], maxsize)

        # Rescale to a common size:
        imga = imga.resize((newx, newy), Image.ANTIALIAS)
        imgb = imgb.resize((newx, newy), Image.ANTIALIAS)

        if not self._colour:
            # Store the images in B/W Int format
            imga = imga.convert('I')
            imgb = imgb.convert('I')

        self._imga = imga
        self._imgb = imgb

        # Store the common image size
        self.x, self.y = newx, newy
    
    

    def _img_int(self, img):
        """Convert an image to a list of pixels."""

        x, y = img.size

        for i in xrange(x):
            for j in xrange(y):
                yield img.getpixel((i, j))

    @property
    def imga_int(self):
        """Return a tuple representing the first image."""

        if not hasattr(self, '_imga_int'):
            self._imga_int = tuple(self._img_int(self._imga))

        return self._imga_int

    @property
    def imgb_int(self):
        """Return a tuple representing the second image."""

        if not hasattr(self, '_imgb_int'):
            self._imgb_int = tuple(self._img_int(self._imgb))

        return self._imgb_int

    @property
    def mse(self):
        """Return the mean square error between the two images."""

        if not hasattr(self, '_mse'):
            tmp = sum((a-b)**2 for a, b in zip(self.imga_int, self.imgb_int))
            self._mse = float(tmp) / self.x / self.y

        return self._mse

    @property
    def psnr(self):
        """Calculate the peak signal-to-noise ratio."""

        if not hasattr(self, '_psnr'):
            self._psnr = 20 * math.log(self._pixel / math.sqrt(self.mse), 10)

        return self._psnr

    @property
    def nrmsd(self):
        """Calculate the normalized root mean square deviation."""

        if not hasattr(self, '_nrmsd'):
            self._nrmsd = math.sqrt(self.mse) / self._pixel

        return self._nrmsd

    @property
    def levenshtein(self):
        """Calculate the Levenshtein distance."""

        if not hasattr(self, '_lv'):
            stra = ''.join((chr(x) for x in self.imga_int))
            strb = ''.join((chr(x) for x in self.imgb_int))

            lv = Levenshtein.distance(stra, strb)

            self._lv = float(lv) / self.x / self.y

        return self._lv
    

        

class ImageCompare(BWImageCompare):
    """Compares two images (colour)."""

    _pixel = 255 ** 3
    _colour = True

    def _img_int(self, img):
        """Convert an image to a list of pixels."""

        x, y = img.size

        for i in xrange(x):
            for j in xrange(y):
                pixel = img.getpixel((i, j))
                yield pixel[0] | (pixel[1]<<8) | (pixel[2]<<16)

    @property
    def levenshtein(self):
        """Calculate the Levenshtein distance."""

        if not hasattr(self, '_lv'):
            stra_r = ''.join((chr(x>>16) for x in self.imga_int))
            strb_r = ''.join((chr(x>>16) for x in self.imgb_int))
            lv_r = Levenshtein.distance(stra_r, strb_r)

            stra_g = ''.join((chr((x>>8)&0xff) for x in self.imga_int))
            strb_g = ''.join((chr((x>>8)&0xff) for x in self.imgb_int))
            lv_g = Levenshtein.distance(stra_g, strb_g)

            stra_b = ''.join((chr(x&0xff) for x in self.imga_int))
            strb_b = ''.join((chr(x&0xff) for x in self.imgb_int))
            lv_b = Levenshtein.distance(stra_b, strb_b)

            self._lv = (lv_r + lv_g + lv_b) / 3. / self.x / self.y

        return self._lv


class FuzzyImageCompare(object):
    """Compares two images based on the previous comparison values."""

    def __init__(self, imga, imgb, lb=1, tol=15):
        """Store the images in the instance."""
        self.logger = ChorusGlobals.get_logger()
        self._imga, self._imgb, self._lb, self._tol = imga, imgb, lb, tol

    def compare(self):
        """Run all the comparisons."""

        if hasattr(self, '_compare'):
            return self._compare

        lb, i = self._lb, 2

        diffs = {
            'levenshtein': [],
            'nrmsd': [],
            'psnr': [],
        }

        stop = {
            'levenshtein': False,
            'nrmsd': False,
            'psnr': False,
        }

        while not all(stop.values()):
            cmpresult = ImageCompare(self._imga, self._imgb, i)

            diff = diffs['levenshtein']
            if len(diff) >= lb+2 and \
                abs(diff[-1] - diff[-lb-1]) <= abs(diff[-lb-1] - diff[-lb-2]):
                stop['levenshtein'] = True
            else:
                diff.append(cmpresult.levenshtein)

            diff = diffs['nrmsd']
            if len(diff) >= lb+2 and \
                abs(diff[-1] - diff[-lb-1]) <= abs(diff[-lb-1] - diff[-lb-2]):
                stop['nrmsd'] = True
            else:
                diff.append(cmpresult.nrmsd)

            diff = diffs['psnr']
            if len(diff) >= lb+2 and \
                abs(diff[-1] - diff[-lb-1]) <= abs(diff[-lb-1] - diff[-lb-2]):
                stop['psnr'] = True
            else:
                try:
                    diff.append(cmpresult.psnr)
                except ZeroDivisionError:
                    diff.append(-1)  # to indicate that the images are identical

            i *= 2

        self._compare = {
            'levenshtein': 100 - diffs['levenshtein'][-1] * 100,
            'nrmsd': 100 - diffs['nrmsd'][-1] * 100,
            'psnr': diffs['psnr'][-1] == -1 and 100.0 or diffs['psnr'][-1],
        }

        return self._compare

    def similarity(self):
        """Try to calculate the image similarity."""

        cmpresult = self.compare()

        lnrmsd = (cmpresult['levenshtein'] + cmpresult['nrmsd']) / 2
        return lnrmsd
        #return min(lnrmsd * cmpresult['psnr'] / self._tol, 100.0)  # TODO: fix psnr!   
    
        
    def GetDiff(self,path,diffimg,mode):
        
        
        tempimg1 = os.path.join(path, 'diff_temp1.png')
        tempimg2 = os.path.join(path, 'diff_temp2.png')
        #print "temp image files: %s,%s" % (tempimg1, tempimg2)
        diffimg = os.path.join(path, diffimg)
        
        sizea, sizeb = self._imga.size, self._imgb.size
        newx = min(sizea[0], sizeb[0])
        newy = min(sizea[1], sizeb[1])
        
        # Rescale to a common size:
        imga = self._imga.resize((newx, newy), Image.ANTIALIAS)
        imgb = self._imgb.resize((newx, newy), Image.ANTIALIAS)
                
        imga.save(tempimg1,'PNG')
        imgb.save(tempimg2,'PNG')
        

        #print cmpexec
        try:
#            diff = subprocess.check_output(command, stderr=subprocess.STDOUT,shell=True)
            command_exec = Utils.whereis("compare")
            if command_exec:
                command = []
                command.append(command_exec)
                command.append('-metric')
                command.append(mode)
                command.append(tempimg1)
                command.append(tempimg2)
                command.append(diffimg)
                self.logger.debug(command)
                diff = Utils.exec_cmd(command)
            else:
                diff = -1
                self.logger.error("cannot generate diff image %s!" % diffimg)
        except subprocess.CalledProcessError, e :            
            diff = -1        
            self.logger.critical("Cannot call compare command with error %s" % e)
        os.remove(tempimg1)
        os.remove(tempimg2)
        
        return diff
    
    '''
    added by Jian histogram way to get similarity
    '''
    def hist_similar(self):
        lh = self._imga.histogram()
        rh = self._imgb.histogram()
        assert len(lh) == len(rh)
        score = sum(1 - (0 if l == r else float(abs(l - r))/max(l, r)) for l, r in zip(lh, rh))/len(lh)
        return score*100
