
# Clothing detection using tensorflow

## 1. What is this?

This is a python pipeline, combining different models to analyze clothes of a picture. If the (python) tensorflow code and the overall pipeline are given here, the models haven't been uploaded.

## 2. How to get started?

- Install tensorflow (>=1.8, python 2.7 or 3). Tensorflow-gpu recommended. 
- Use your own models.
- Update the global variables in main.py (especially for folder and model paths)
- python main.py

This pipeline detects clothes, but you can reuse it for whatever purpose


## 3. Pipeline description


![alt text](https://raw.githubusercontent.com/MatthieuBlais/tensorflow-clothing-detection/master/pipeline.png)

1. We load an image
2. We remove the background with deeplab (we extract the persons)
3. We detect the objects we want (here, the clothes. We also make sure that we can't detect that a person wears a dress, a top and a t-shirt at the same time!) 
4. We extract the last layer of an inception model. This is used to analyze similarity between clothes
5. We could apply additional classifiers here but as they are not ready yet, we just save everything.
