"""Functions for finding the foreground in an image with a clean
background (i.e. mostly white or black)"""

from __future__ import division
import numpy as np
from crash_kiss.config import BLACK, WHITE, config
import crash_kiss.util as util


#@profile
def find_foreground(img, background, config):
    """Find the foreground of the image by subracting each RGB element
    in the image by the background. If the background has been reduced
    to a simple int or float, we'll try to avoid calling `np.abs`
    by checking to see if the background value is near 0 or 255."""
    threshold = config["threshold"]
    mask = _compare_pixels(img, background, threshold)
    return mask
    
    """
    mask = background - img[:, :, 0] > threshold

    print np.count_nonzero(mask)
    mask[mask==0] = background - img[mask==0][:, :, 1] > threshold
    print np.count_nonzero(mask)
    mask[mask==0] = background - img[:, :, 2][mask==0] > threshold
    print np.count_nonzero(mask)
    return mask
    
    for color in range(img.shape[-1]):
        diff = background - img[:, :, color][mask==0] > threshold
        mask[mask==0] = diff
    return mask 
    """

    return _compare_pixels(img, background, threshold)


#@profile
def _compare_pixels(img, background, threshold):
    """Compare a 2-D or 3-D image array
    to a background value given a certain threshold"""
    is_num = isinstance(background, int)
    if background - BLACK <= 5:
        diff = img - background > threshold
    elif WHITE - background <= 5:
        diff = background - img > threshold
    else:
        diff = np.abs(img - background) > threshold
    if len(diff.shape) == 3:
        diff = np.any(diff, axis=2)  # we're using a 3D array
    return diff
   

def simplify_background(background, config):
    """See if the background's RGB elements are similar.
    If each element in the background is similar enough, we can do a simple
    array - int operation instead of the more expensive array - [R, G, B]
    or the even pricier array - <array of shape (NROWS, 1, 3)> operation."""
    while isinstance(background, np.ndarray):
        bg_change_tolerance = config["bg_change_tolerance"]
        bmax, bmin = background.max(axis=0), background.min(axis=0)
        diff = (bmax - bmin) < bg_change_tolerance
        if len(background.shape) >= 2:
            diff = np.all(diff)
        if diff:
            background = np.median(background, axis=0)
        else:
            break  # we've simplified the background as much as we can
    return background


@profile
def center_smash(img, foreground, maxlen):
    """Move the rows of each subject together until they touch.
    Write over the vacated space with whatever the row's negative space
    is (probably white or transparent pixels)."""
    fg = foreground[:]
    fg_l, fg_r = util.bisect_img(fg)
    fg_l = util.invert_horizontal(fg_l)
    mid_idx = fg_l.shape[1]  # start idx for LHS of `right`
    l_start = np.argmax(fg_l, axis=1)
    r_start = np.argmax(fg_r, axis=1)
    offs = r_start - l_start
    for img_row, offs, fg_row in zip(img, offs, fg):
        sub_row = img_row[fg_row]
        sub_len = sub_row.shape[0]
        halflen = sub_len // 2  # always truncate; we can't do any better
        start_idx = mid_idx - halflen
        stop_idx = start_idx + sub_len
        img_row[start_idx: stop_idx] = sub_row
        img_row[:start_idx] = WHITE
        img_row[stop_idx:] = WHITE
    img[:maxlen] = WHITE
    img[-maxlen:] = WHITE


def reveal_foreground(subject):
    subject.img[subject.foreground] = BLACK


def reveal_background(subject):
    subject.img[subject.background] = WHITE



