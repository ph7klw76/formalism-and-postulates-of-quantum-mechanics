"""Local static server with byte-range video seeking (stdlib only)."""
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import argparse,functools,re
from urllib.parse import urlsplit,unquote

class RangeHandler(SimpleHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    base_path='/'
    def translate_path(self,path):
        clean=unquote(urlsplit(path).path)
        if self.base_path!='/' and not clean.startswith(self.base_path):
            return str(Path(self.directory)/'__outside_repository__')
        return super().translate_path('/'+clean.removeprefix(self.base_path))
    def send_head(self):
        self.remaining=None
        path=Path(self.translate_path(self.path))
        if not self.headers.get('Range') or not path.is_file():return super().send_head()
        match=re.fullmatch(r'bytes=(\d*)-(\d*)',self.headers['Range'])
        size=path.stat().st_size
        if not match or not size:
            self.send_error(416);return None
        left,right=match.groups()
        if not left and not right:self.send_error(416);return None
        start=int(left) if left else max(0,size-int(right))
        end=min(size-1,int(right)) if left and right else size-1
        if start>=size or start>end:
            self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.send_header('Content-Length','0');self.end_headers();return None
        stream=path.open('rb');stream.seek(start);self.remaining=end-start+1
        self.send_response(206);self.send_header('Content-Type',self.guess_type(str(path)))
        self.send_header('Content-Length',str(self.remaining));self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.send_header('Accept-Ranges','bytes');self.end_headers();return stream
    def copyfile(self,source,outputfile):
        try:
            if self.remaining is None:return super().copyfile(source,outputfile)
            while self.remaining:
                data=source.read(min(self.remaining,256*1024))
                if not data:break
                outputfile.write(data);self.remaining-=len(data)
        except (BrokenPipeError,ConnectionResetError):
            # Browsers routinely cancel an old range when the learner seeks.
            return

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]/'website/dist'
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);p.add_argument('--directory',default=str(root));p.add_argument('--base-path',default='/');args=p.parse_args()
    root=Path(args.directory).resolve();RangeHandler.base_path=args.base_path
    server=ThreadingHTTPServer(('127.0.0.1',args.port),functools.partial(RangeHandler,directory=str(root)))
    print(f'Course preview: http://127.0.0.1:{args.port}{args.base_path}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
