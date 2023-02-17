#%%
import ee
ee.Initialize()

import geemap
import os
import xarray as xr
import rioxarray
import numpy as np

#%%
#convert from sigma_0 to gamma_0
def toGamma0(image):
  gamma0 = image.select('VV').subtract(image.select('angle').multiply(np.pi/180.0).cos().log10().multiply(10.0));
  return gamma0.copyProperties(image).copyProperties(image,['system:time_start']);

# mosaic images with the same date that have been spatially split
def mosaicByDate(imcol):
    imlist = imcol.toList(imcol.size())
    unique_dates = imlist.map(lambda im: ee.Image(im).date().format('YYYY-MM-dd')).distinct()
    def mosaic_imlist(d):
        d = ee.Date(d)
        im = imcol.filterDate(d, d.advance(1, 'day')).mosaic() 
        return im.set(
        'system:time_start', d.millis(), 
        'system:id', d.format('YYYY-MM-dd'));
    return ee.ImageCollection(unique_dates.map(mosaic_imlist))

#%%
# define year of the analysis

START_DATE = '2016-01-01'; #no image before
END_DATE = '2020-01-01'; #exclusive = ie., until 2019-12-31

# define image projection 

crs = 'EPSG:4326'

#%%
# define your area of interest

aoi_shp = 'test.shp'
#aoi_shp = 'gadm41_GUF_0.shp'
aoi = geemap.shp_to_ee(aoi_shp)

# choose a path for your output directory. This is where you will have saved all the images in the collection

outdir = 'output_image/'

#%%
collection = (ee.ImageCollection('COPERNICUS/S1_GRD')
          .filterBounds(aoi).filterDate(ee.Date(START_DATE), ee.Date(END_DATE))
          .filter(ee.Filter.eq('instrumentMode', 'IW'))
          .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
          .filterMetadata('transmitterReceiverPolarisation', 'equals', ['VV', 'VH'])
          .filterMetadata('resolution_meters', 'equals', 10)
          .map(toGamma0)
          .map(lambda image:image.clip(aoi.geometry())))

# select VV polarization
vv = collection.select(['VV']) 
vv_size = vv.size().getInfo()
print('original size of Image Stack: ', vv_size)

#get image dates
imlist = vv.toList(vv.size())
unique_dates = imlist.map(lambda im:ee.Image(im).date().format('YYYY-MM-dd')).distinct()
date_list = unique_dates.getInfo()

#mosaic images with same date
vv_mosaic = mosaicByDate(vv)
mosaic_size = vv_mosaic.size().getInfo()
print('size of Image Stack after mosaicking: ' ,mosaic_size)

#%%
#aaa = vv_mosaic.first()

#Map = geemap.Map(center = (4.177, -52.521), zoom = 9)
#Map.addLayer(aaa, {'min': 0, 'max':100, 'palette': ['purple', 'yellow']}, 'xxx', True, 1)
#Map

#%%
#export Image Collection to Google Drive
vv_mosaic_list = vv_mosaic.toList(vv_mosaic.size())

for i in range(vv_mosaic_list.length().getInfo()):
    image = ee.Image(vv_mosaic_list.get(i))
    id = image.id()
    img_name = id.replace('/', '_')
    export_task = ee.batch.Export.image.toDrive(
        image=image,
        description='s1_test',
        folder='s1_dist_gf',
        region=aoi,
        scale=10,
        crs='EPSG:4326',
        maxPixels=1e13,
        fileFormat='GeoTIFF'
    )
    export_task.start()
# %%
