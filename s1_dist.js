//convert from sigma_0 to gamma_0
var toGamma0 = function(image) {
    var gamma0 = image.select('VV').subtract(image.select('angle').multiply(Math.PI/180.0).cos().log10().multiply(10.0));
    return gamma0.copyProperties(image).copyProperties(image,['system:time_start']);
  };
  
  // mosaic images with the same date that have been spatially split
  //var mosaicByDate = function(imcol) {
  //    imlist = imcol.toList(imcol.size())
  //    unique_dates = imlist.map(lambda im: ee.Image(im).date().format("YYYY-MM-dd")).distinct()
  //    var mosaic_imlist = function(d) {
  //        d = ee.Date(d)
  //        im = imcol.filterDate(d, d.advance(1, "day")).mosaic() 
  //        return im.set(
  //        "system:time_start", d.millis(), 
  //        "system:id", d.format("YYYY-MM-dd"));
  //    };
  //    return ee.ImageCollection(unique_dates.map(mosaic_imlist))
  //};
  
  // define year of the analysis
  var START_DATE = ee.Date("2016-01-01"); //no image before
  var END_DATE = ee.Date("2020-01-01"); //exclusive = ie., until 2019-12-31
  
  // define image projection 
  var crs = ee.String("EPSG:4326");
  
  // define your area of interest
  var aoi_test = ee.FeatureCollection("projects/ee-epingchris/assets/gadm41_GUF_0"),
      aoi = ee.FeatureCollection("projects/ee-epingchris/assets/test");
  
  var collection = ee.ImageCollection('COPERNICUS/S1_GRD')
      .filterBounds(aoi).filterDate(ee.Date(START_DATE), ee.Date(END_DATE))
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
  var unique_dates = imlist.map(function(im) {return ee.Image(im).date().format("YYYY-MM-dd")}).distinct();
  var date_list = unique_dates.getInfo();
  
  //mosaic images with same date
  //vv_mosaic = mosaicByDate(vv)
  //mosaic_size = vv_mosaic.size().getInfo()
  //print('size of Image Stack after mosaicking: ' ,mosaic_size)
  
  //var aaa = vv.first();
  Map.setCenter(-52.521, 4.177, 9);
  Map.addLayer(vv, {'min': 0, 'max':100, 'palette': ['purple', 'yellow']}, 'xxx', true, 1);
  Map;
  
  Export.image.toDrive({
      image: vv,
      description: 's1_dist_gf',
      folder: 'export',
      region: aoi,
      scale: 10,
      crs: 'EPSG:4326',
      formatOptions: {
          cloudOptimized: true
      },
      maxPixels: 1E13
  });