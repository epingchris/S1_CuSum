#%%
import os, glob
import xarray as xr
import rioxarray as rxr
import datetime as dt
import pandas as pd

import pyproj
pyproj.datadir.set_data_dir(r'C:\\Users\\E-Ping Rau\\anaconda3\\pkgs\\proj-9.1.1-heca977f_2\\Library\\share\\proj')

#%%
# Convert Image Collection to xarray ----
#list all downloaded images
outdir = '.\\s1_gfla\\'
vv_tifs = os.listdir(outdir)
file_list = list(filter(os.path.isfile, glob.glob(outdir + '*.tif')))
    
#sort images by date (simply sort by file name is possible because date was included in file name)
file_list.sort()

#create the date list from path name
date_list = []
for i, path in enumerate(file_list):
    date_list.append(path.replace('.\\s1_gfla\\s1_gfla_', '').replace('.tif', '').replace('_', '-'))

#%%
# Loop through the list, open image as xarray and assign time label ----
index = 0
for file, date in zip(file_list, date_list):
    da = rxr.open_rasterio(file, masked = True)
    dt = dt.datetime.strptime(date, '%Y-%m-%d')
    dt = pd.to_datetime(dt)
    da = da.assign_coords(time = dt)
    da = da.expand_dims(dim = 'time')
    list_da.append(da)
    print(str(index) + ' successful\n')
    index += 1

#when using rioxarray to load, errors may arise because PROJ library path is not set
#check this: https://gis.stackexchange.com/questions/363743/initalize-pyproj-correctly

#stack data arrays in list
ds = xr.combine_by_coords(list_da)

#%%
# Use intervals ----
#find intervals of 360 days
interv = [0]
i = 0
j = 1
day_diff = 0
while True:
    a = dt.datetime.strptime(date_list[i], '%Y-%m-%d')
    b = dt.datetime.strptime(date_list[j], '%Y-%m-%d')
    day_diff = int((b - a) / dt.timedelta(days = 1))
    if day_diff >= 360:
        interv.append(j)
        i = j
        continue
    j += 1
    if j == len(date_list):
        if(interv[-1] != j - 1):
            interv.append(j - 1)
        break

#check
[str(dt.datetime.strptime(date_list[i], '%Y-%m-%d')) + ' ; ' for i in interv]

#loop through the list in intervals, open image as xarray and assign time label
list_da = []

index = 0
for i in range(0, len(interv)):
    file_chunk = file_list[interv[i]:interv[i + 1]]
    date_chunk = date_list[interv[i]:interv[i + 1]]
    da_chunk = xr.concat([rxr.open_rasterio(file, masked = True) for file in file_chunk], dim = 'time')
    dt_chunk = [dt.datetime.strptime(date, '%Y-%m-%d') for date in date_chunk]
    dt_chunk = [pd.to_datetime(dt) for dt in dt_chunk]
    da_chunk = da_chunk.assign_coords(time = dt_chunk)
    list_da.append(da_chunk)
    print(str(index) + ' successful\n')
    index += 1

#when using rioxarray to load, errors may arise because PROJ library path is not set
#check this: https://gis.stackexchange.com/questions/363743/initalize-pyproj-correctly

#stack data arrays in list
ds = xr.combine_by_coords(list_da)

# CumSum implementation ----
#%%
# get timeseries mean
dsmean = ds.mean(dim='time')
#get time series residual
R = ds-dsmean 
# get time series cumulative sum
S = R.cumsum(dim="time") 
# get maximum of the cumulative sum
Smax= S.max(dim="time")     
# the threshold is calculated as 99th percentile of the CuSum max
threshold = np.percentile(Smax, 99) 
# filter cumulative sum array by year of interest
Sfilt_time = S.sel(time=year) 
# convert to DOY
Sfilt_time['time'] = Sfilt_time["time.dayofyear"]
# spatially filter by 99th percentile
Sfilt_n = Sfilt_time.where(Sfilt_time>= threshold,np.nan)
# determine where you have valid data
mask = Sfilt_n['time'].isel(time=0).notnull()  
#convert Nan to calculate maximum
Sfilt_n2 = Sfilt_n.fillna(-9999)
# get the date where the curve reaches the maximum value
Sfilt_max = Sfilt_n2.isel(time = Sfilt_n2.argmax('time')).where(mask) 

max_values = Sfilt_max.where(Sfilt_max> -9999,np.nan)
max_dates = Sfilt_n.idxmax(dim="time")

max_values.name = 'Smax'
max_dates.name = 'doy'
Save outputs
intensityName = 'path/output/folder/Smax.tif'   # path to your folder for Smax intensity image
dateName = 'path/output/folder/Dates.tif'       # path to your folder for Date image

max_values_raster = max_values.rio.write_crs(crs)
max_values_raster.rio.to_raster(intensityName,compress='LZMA')

max_dates_raster = max_dates.rio.write_crs(crs)
max_dates_raster.rio.to_raster(dateName,compress='LZMA')