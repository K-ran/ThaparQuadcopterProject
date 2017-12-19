var admin = require("firebase-admin");
var fs = require('fs');
const path = require('path');
var uploader = require('file-uploader') 

// uploader options
var options = {
  host : '104.196.253.182',
  port : 8080,
  path : '/upload',
  method : 'POST',
  name : 'image',
  encoding : 'utf8'
}


const   { exec }   = require('child_process');

// console.log('after calling readFile');

// Change according to your crediantials.
var serviceAccount = require(path.join(__dirname, "service.json"));

// Change according to your firebase account.
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  databaseURL: "https://capstone-f2b6f.firebaseio.com"
});


// Get a database reference to our posts.
var db = admin.database();
var refGps = db.ref("copter_location/");
var refLog = db.ref("LOG/");


// Change the string after --connect if required.
console.log('Starting waypoint Program');
exec('python '+path.join(__dirname, 'waypoint.py')+' --connect /dev/ttyACM0', (err, stdout, stderr) => {
  if (err) {
    console.error(err);
    return;
  }
});

console.log('Starting Camera server');
exec('python2 '+path.join(__dirname, 'cam.py'), (err, stdout, stderr) => {
  if (err) {
    console.error(err);
    return;
  }
});


//Sends current coordinate 
fs.watch(path.join(__dirname, 'coordinates.txt'), 'utf8', function(event,file) {
    // console.log('File Changed ...');
    fileStr = fs.readFileSync(path.join(__dirname, 'coordinates.txt'),'utf8').split(",");
    lat = fileStr[0]
    lon = fileStr[1]
    if(lat && lon){
      try {
        // statements
        refGps.set({
          'latitude':parseFloat(lat),
          'longitude':parseFloat(lon),
          'valid': true
        });
      } catch(e) {
        // statements
        console.log(e);
      }
    }
});

fs.watch(path.join(__dirname, 'logs.txt'), 'utf8', function(event,file) {
  fileStr = fs.readFileSync(path.join(__dirname, 'logs.txt'),'utf8').split('\n');
  log = fileStr[fileStr.length-2]
  console.log(log);
  try {
    db.ref().update({
      "Log":log
    });
  } catch(e) {
    // statements
    console.log(e);
  }
});

fs.watch(path.join(__dirname, 'status.txt'), 'utf8', function(event,file) {
  fileStr = fs.readFileSync(path.join(__dirname, 'status.txt'),'utf8')
  try {
    db.ref().update({
      "status":fileStr
    });
  } catch(e) {
    console.log(e);
  }
});

fs.watch(path.join(__dirname, 'images/'), 'utf8', function(event,file) {
  if(file.split('.').length==2){ 
    if(fs.existsSync(path.join(__dirname, 'images/')+file)){
      console.log('Uploading: '+file);

      try{
        uploader.postFile(options,path.join(__dirname, 'images/')+file,'',function(err, res) {
          firstName = file.split('.')[0];
          fileStr = fs.readFileSync(path.join(__dirname, 'images/')+firstName,'utf8').split(",");
          lat = fileStr[0]
          lon = fileStr[1]
          db.ref("aerial_images/"+firstName).set({
            "latitude":parseFloat(lat),
            "longitude":parseFloat(lon)
          });
          console.log('Done Uploading: '+file)
        })
      }catch(e){
        console.log(e);
      }
    }
  }
});
  