//convert from sigma_0 to gamma_0
var toGamma0 = function(image) {
    var gamma0 = image.select('VV').subtract(image.select('angle').multiply(Math.PI/180.0).cos().log10().multiply(10.0));
    return gamma0.copyProperties(image).copyProperties(image,['system:time_start']);
  };
  
  // mosaic images with the same date that have been spatially split
  var mosaicByDate = function(imcol) {
      imlist = imcol.toList(imcol.size());
      unique_dates = imlist.map(function(im) {return ee.Image(im).date().format('YYYY-MM-dd')}).distinct();
      var mosaic_imlist = function(d) {
          d = ee.Date(d);
          var im = imcol.filterDate(d, d.advance(1, 'day')).mosaic();
          return im.set(
          'system:time_start', d.millis(), 
          'system:id', d.format('YYYY-MM-dd'));
      };
      return ee.ImageCollection(unique_dates.map(mosaic_imlist));
  };
  
  // define year of the analysis
  var start_date = ee.Date('2016-01-01'); //no image before
  var end_date = ee.Date('2020-01-01'); //exclusive = ie., until 2019-12-31
  
  // define image projection 
  var crs = ee.String('EPSG:4326');
  
  // define your area of interest
  //var aoi = ee.FeatureCollection('projects/ee-epingchris/assets/gadm41_GUF_0');
  var aoi = ee.FeatureCollection('projects/ee-epingchris/assets/test');
  
  var collection = ee.ImageCollection('COPERNICUS/S1_GRD')
      .filterBounds(aoi).filterDate(ee.Date(start_date), ee.Date(end_date))
      .filter(ee.Filter.eq('instrumentMode', 'IW'))
      .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
      .filterMetadata('transmitterReceiverPolarisation', 'equals', ['VV', 'VH'])
      .filterMetadata('resolution_meters', 'equals', 10)
      .map(toGamma0)
      .map(function(image) {return image.clip(aoi.geometry())});
  
  // select VV polarization
  var vv = collection.select(['VV']);
  var vv_size = vv.size().getInfo();
  console.log('original size of Image Stack: ' + vv_size);
  
  //get image dates
  var imlist = vv.toList(vv.size());
  var unique_dates = imlist.map(function(im) {return ee.Image(im).date().format('YYYY-MM-dd')}).distinct();
  var date_list = unique_dates.getInfo();
  
  //mosaic images with same date
  var vv_mosaic = mosaicByDate(vv);
  var mosaic_size = vv_mosaic.size().getInfo();
  console.log('size of Image Stack after mosaicking: ' + mosaic_size);
  
  var vv_mosaic_list = vv_mosaic.toList(vv_mosaic.size());
  
  for (var i = 0; i < vv_mosaic_list.length().getInfo(); i++) {
    var image = ee.Image(vv_mosaic_list.get(i));
    var id = image.id();
    var img_name = id.replace('/', '_');
    var exportTask = ee.batch.Export.image.toDrive({
      image: image,
      description: 's1_test' + img_name,
      fileNamePrefix: 's1_test' + img_name,
      folder: 'myFolder',
      region: aoi,
      scale: 10,
      crs: 'EPSG:4326',
      maxPixels: 1e13,
      fileFormat: 'GeoTIFF'
    });
    exportTask.start();
  };
  
  //var batch = require('users/fitoprincipe/geetools:batch');
  
  //batch.Download.ImageCollection.toDrive(vv, 's1_dist_gf', {
  //  name: 'S1_gf_{system_date}',
  //  scale: 10,
  //  region: aoi,
  //  crs: 'EPSG:4326',
  //  maxPixels: 1E13});