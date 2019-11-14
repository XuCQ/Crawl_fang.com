import urllib.request,urllib,http.client
import urllib.parse
import json
# key
# o1EOCWVhKSQOr2V9GXsQ7zmI2KO8CSpP
# wU3ZlXOKopbk78vjeZiSkDeo
class xBaiduMap:
    def __init__(self,key='wU3ZlXOKopbk78vjeZiSkDeo'):
        self.host = 'http://api.map.baidu.com'
        self.path = '/geocoder/v2/?'
        self.param = {'address': None, 'output': 'json', 'ak': key, 'location': None, 'city': None}

    def getLocation(self, address, city=None):
        rlt = self.geocoding('address', address, city)
        if rlt != None:
            l = rlt['result']
            if isinstance(l, list):
                return None
            return l['location']['lat'], l['location']['lng']
    def getAddress(self, lat, lng):
        rlt = self.geocoding('location', "{0},{1}".format(lat,lng))
        if rlt != None:
            l = rlt['result']
            return l['formatted_address']
            # ld=rlt['result']['addressComponent']
            # print(ld['city']+';'+ld['street'])
            #
    def geocoding(self, key, value, city=None):
        if key == 'location':
            # print(value)
            if 'city' in self.param:
                del self.param['city']
            if 'address' in self.param:
                del self.param['address']

        elif key == 'address':
            if 'location' in self.param:
                del self.param['location']
            if city == None and 'city' in self.param:
                del self.param['city']
            else:
                self.param['city'] = city
        self.param[key] = value
        # print(self.host + self.path + urllib.parse.urlencode(self.param))
        r = urllib.request.urlopen(self.host + self.path + urllib.parse.urlencode(self.param))
        # urllib库里面有个urlencode函数，可以把key - value这样的键值对转换成我们想要的格式，返回的是a = 1 & b = 2 这样的字符串
        rlt = json.loads(r.read())
        if rlt['status'] == 0:
            return rlt
        else:
            print
            "Decoding Failed"
            return None
