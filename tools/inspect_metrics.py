import urllib.request

url = 'http://127.0.0.1:8000/api/tasks/metrics/'
print('Requesting', url)
try:
    resp = urllib.request.urlopen(url)
    body = resp.read().decode('utf-8')
    print('Status:', resp.getcode())
    print('Body:\n', body)
except Exception as e:
    print('Error:', repr(e))
    try:
        import urllib.error
        if isinstance(e, urllib.error.HTTPError):
            body = e.read().decode('utf-8')
            print('HTTPError body:\n', body)
    except Exception:
        pass
