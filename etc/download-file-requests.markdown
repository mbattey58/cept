# Dowloading files with requests


[simple requests call](https://dzone.com/articles/simple-examples-of-downloading-files-using-python)
```python
import requests
url = 'https://www.python.org/static/img/python-logo@2x.png'
myfile = requests.get(url)
open('c:/users/LikeGeeks/downloads/PythonImage.png', 'wb').write(myfile.content)
```

[streaming with fixed buffer size](https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests)
```python
def download_file(url):
    local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk: 
                f.write(chunk)
    return local_filename
```
