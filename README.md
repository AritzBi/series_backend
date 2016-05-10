openshift-mongo-flask-example
=============================

This is the code to go along with the [OpenShift blog piece](https://www.openshift.com/blogs/rest-web-services-with-python-mongodb-and-spatial-data-in-the-cloud-part-2) on how to use Flask (python) with MongoDB to create a REST like web service with spatial data
**Please note that this only works with Python-2.6 cartridge**

Running on OpenShift
----------------------------

Create an account at https://www.openshift.com

Create a python application with MongoDB

    rhc app create pythonws python-2.6 mongodb-2 --from-code git://github.com/openshift-quickstart/openshift-mongo-flask-example.git
    
or you can do this

    rhc app create pythonws python-2.6 mongodb-2
    cd pythonws
    git remote add upstream -m master git://github.com/openshift-quickstart/openshift-mongo-flask-example.git
    git pull -s recursive -X theirs upstream master
    git push
    
To add the data to the MongoDB instance please follow the instructions on this blog:
[Mongo Spatial on OpenShift](https://www.openshift.com/blogs/spatial-mongodb-in-openshift-be-the-next-foursquare-part-1)

Now, ssh into the application.

Add the data to a collection called parkpoints:

    mongoimport -d pythonws -c parkpoints --type json --file $OPENSHIFT_REPO_DIR/parkcoord.json  -h $OPENSHIFT_MONGODB_DB_HOST  -u admin -p $OPENSHIFT_MONGODB_DB_PASSWORD --port $OPENSHIFT_MONGODB_DB_PORT

    
Create the spatial index on the documents:

    mongo
    use pythonws
    db.parkpoints.ensureIndex( { pos : "2d" } );

Once the data is imported you can now checkout your application at:

    http://pythonws-$yournamespace.rhcloud.com/ws/parks
 
License
-------

This code is dedicated to the public domain to the maximum extent permitted by applicable law, pursuant to CC0 (http://creativecommons.org/publicdomain/zero/1.0/)
