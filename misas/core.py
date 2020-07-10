# AUTOGENERATED! DO NOT EDIT! File to edit: 01_local_interpret.ipynb (unless otherwise specified).

__all__ = ['Fastai1_model', 'get_generic_series', 'plot_series', 'plot_frame', 'gif_series', 'eval_generic_series',
           'rotationTransform', 'get_rotation_series', 'eval_rotation_series', 'cropTransform', 'get_crop_series',
           'eval_crop_series', 'brightnessTransform', 'get_brightness_series', 'eval_bright_series',
           'contrastTransform', 'get_contrast_series', 'eval_contrast_series', 'zoomTransform', 'get_zoom_series',
           'eval_zoom_series', 'dihedralTransform', 'get_dihedral_series', 'eval_dihedral_series', 'resizeTransform',
           'eval_resize_series']

# Internal Cell
from fastai.vision import *
import pandas as pd
from tqdm.notebook import tqdm
import matplotlib.pyplot as plt
import gif
import math
import numpy as np
import torchvision

# Internal Cell
def dice_by_component(predictedMask, trueMask, component = 1):
    dice = Tensor([1])
    pred = predictedMask.data == component
    msk = trueMask.data == component
    intersect = pred&msk
    total = pred.sum() + msk.sum()
    if total > 0:
        dice = 2 * intersect.sum().float() / total
    return dice.item()

# Cell
class Fastai1_model:
    def __init__(self, github, model):
        self.trainedModel = torch.hub.load(github,model)
        self.resize256 = lambda x: x.resize(256)

    def prepareSize(self, item):
        return self.resize256(item)

    def predict(self, image):
        return self.trainedModel.predict(image)

# Cell
def get_generic_series(image,
        model,
        transform,
        truth=None,
        tfm_y=False,
        start=0,
        end=180,
        step=30,
        log_steps=False,
    ):
    series = []
    trueMask = None
    steps = np.arange(start,end,step)
    if log_steps:
        steps = np.exp(np.linspace(log(start),log(end),int((end-start)/step)))
    for param in tqdm(steps, leave=False):
        img = image.clone()
        img = transform(img, param)
        if hasattr(model,"prepareSize"):
            img = model.prepareSize(img)
        pred = model.predict(img)[0]
        series.append([param,img,pred])
        if truth:
            trueMask = truth.clone()
            if tfm_y:
                trueMask = transform(trueMask, param)
            if hasattr(model,"prepareSize"):
                trueMask = model.prepareSize(trueMask)
        series[-1].append(trueMask)
    return series

# Cell
def plot_series(
        series,
        nrow=1,
        figsize=(16,6),
        param_name='param',
        overlay_truth=False
    ):
    fig, axs = plt.subplots(nrow,math.ceil(len(series)/nrow),figsize=figsize)
    for element, ax in zip(series, axs.flatten()):
        param,img,pred,truth = element
        img.show(ax=ax, title=f'{param_name}={param:.2f}')
        pred.show(ax=ax)
        if overlay_truth and truth:
            truth.show(ax=ax,alpha=.2)

# Cell
@gif.frame
def plot_frame(param, img, pred, param_name="param",**kwargs):
    _,ax = plt.subplots(**kwargs)
    img.show(ax,title=f'{param_name}={param:.2f}')
    pred.show(ax)

# Cell
def gif_series(series, fname, duration=150, param_name="param"):
    frames = [plot_frame(*x[:3], param_name=param_name) for x in series]
    gif.save(frames, fname, duration=duration)

# Cell
def eval_generic_series(
        image,
        mask,
        model,
        transform_function,
        start=0,
        end=360,
        step=5,
        param_name="param",
        mask_transform_function=None,
        components=['bg', 'c1','c2']
    ):
    results = list()
    for param in tqdm(np.arange(start, end, step), leave=False):
        img = image.clone()
        img = transform_function(img, param)
        trueMask = mask.clone()
        if mask_transform_function:
            trueMask = mask_transform_function(trueMask, param)
        if hasattr(model,"prepareSize"):
            img = model.prepareSize(img)
            trueMask = model.prepareSize(trueMask)
        prediction = model.predict(img)[0]
        # prediction._px = prediction._px.float()
        result = [param]
        for i in range(len(components)):
            result.append(dice_by_component(prediction, trueMask, component = i))
        results.append(result)

    results = pd.DataFrame(results,columns = [param_name, *components])
    return results

# Cell
def rotationTransform(image, deg):
    return image.rotate(int(deg))

def get_rotation_series(image, model, start=0, end=360, step=60, **kwargs):
    return get_generic_series(image,model,rotationTransform, start=start, end=end, step=step, **kwargs)

# Cell
def eval_rotation_series(image, mask, model, step=5, start=0, end=360, **kwargs):
    return eval_generic_series(
        image,
        mask,
        model,
        rotationTransform,
        start=start,
        end=end,
        step=step,
        mask_transform_function=rotationTransform,
        param_name="deg",
        **kwargs
    )

# Cell
def cropTransform(image, pxls):
    image = image.crop_pad(int(pxls))
    image = image.rotate(180)
    image = image.crop_pad(256, padding_mode="zeros")
    image = image.rotate(180)
    return image

def get_crop_series(image, model, start=56, end=257, step=50, **kwargs):
    return get_generic_series(image,model,cropTransform, start=start, end=end, step=step, **kwargs)

# Cell
def eval_crop_series(image, mask, model, step=5, start=56, end=256, **kwargs):
    return eval_generic_series(
        image,
        mask,
        model,
        cropTransform,
        start=start,
        end=end,
        step=step,
        mask_transform_function=rotationTransform,
        param_name="pixels",
        **kwargs
    )

# Cell
def brightnessTransform(image, light):
    return image.brightness(light)

def get_brightness_series(image, model, start=0.05, end=1, step=.1, **kwargs):
    return get_generic_series(image,model,brightnessTransform, start=start, end=end, step=step, **kwargs)

# Cell
def eval_bright_series(image, mask, model, start=0.05, end=.95, step=0.05, param_name="brightness", **kwargs):
    return eval_generic_series(
        image,
        mask,
        model,
        brightnessTransform,
        start=start,
        end=end,
        step=step,
        param_name=param_name,
        **kwargs
    )

# Cell
def contrastTransform(image, scale):
    return image.contrast(scale)

def get_contrast_series(image, model, start=0.1, end=7.01, step=1, **kwargs):
    return get_generic_series(image,model,contrastTransform, start=start, end=end, step=step, **kwargs)

# Cell
def eval_contrast_series(image, mask, model, start=0.1, end=7.1, step=0.5, param_name="contrast", **kwargs):
    return eval_generic_series(
        image,
        mask,
        model,
        contrastTransform,
        start=start,
        end=end,
        step=step,
        param_name=param_name,
        **kwargs
    )

# Cell
def zoomTransform(image, scale):
    image = image.crop_pad(int(scale), padding_mode="zeros")
    return image

def get_zoom_series(image, model, start=56, end=500, step=50, **kwargs):
    return get_generic_series(image,model,zoomTransform, start=start, end=end, step=step, **kwargs)

# Cell
def eval_zoom_series(image, mask, model, step=10, start=56, end=500, **kwargs):
    return eval_generic_series(
        image,
        mask,
        model,
        zoomTransform,
        start=start,
        end=end,
        step=step,
        mask_transform_function=zoomTransform,
        param_name="scale",
        **kwargs
    )

# Cell
def dihedralTransform(image, sym_im):
    return image.dihedral(k=int(sym_im))

def get_dihedral_series(image, model, start=0, end=8, step=1, **kwargs):
    return get_generic_series(image,model,dihedralTransform, start=start, end=end, step=step, **kwargs)

# Cell
def eval_dihedral_series(image, mask, model, start=0, end=8, step=1, param_name="k", **kwargs):
    return eval_generic_series(
        image,
        mask,
        model,
        dihedralTransform,
        start=start,
        end=end,
        step=step,
        param_name=param_name,
        mask_transform_function=dihedralTransform,
        **kwargs
    )

# Cell
def resizeTransform(image, size):
    return image.resize(int(size)).clone()

# Cell
def eval_resize_series(image, mask, model, start=25, end=260, step=5, param_name="px", **kwargs):
    return eval_generic_series(
        image,
        mask,
        model,
        resizeTransform,
        start=start,
        end=end,
        step=step,
        param_name=param_name,
        mask_transform_function=resizeTransform,
        **kwargs
    )