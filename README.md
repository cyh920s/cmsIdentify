<h1>cmsIdentify</h1>
cmsIdentify是小型的cms指纹识别工具，指纹库来源于互联网。防止扫描的时候ip被封，可选择用代理扫描，代理扫描效率会低一些

<h2>使用示例：</h2>

```
python3 main.py -u http://www.xxx.com -p true
```
<h2>配置</h2>

```
optional arguments:
  -u URL, --url URL		     	请设置URL链接
  -p PROXY, --proxy PROXY		设置是否用代理匹配cms指纹，默认为False
```
