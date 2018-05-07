from bson import SON, ObjectId
from datetime import datetime, timedelta

minmax = {
    'item_title': 'Min Max Values Aggregation',
    'datasource': {
        'source': 'values',
        'aggregation': {

            'pipeline': [
                { 
            "$match" : {
                "p" : {
                    "$ne" : 0
                }, 
                "time" : {
                    "$gte" : datetime.now() - timedelta(hours = 24)
                }
            }
        }, 
        { 
            "$group" : {
                "_id" : None, 
                "max_t" : {
                    "$max" : "$t"
                }, 
                "min_t" : {
                    "$min" : "$t"
                }, 
                "max_p0" : {
                    "$max" : "$p0"
                }, 
                "min_p0" : {
                    "$min" : "$p0"
                }, 
                "max_rh" : {
                    "$max" : "$rh"
                }, 
                "min_rh" : {
                    "$min" : "$rh"
                }
            }
        },
            ]

        }
    }
}
