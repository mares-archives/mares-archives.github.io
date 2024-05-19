import os
from os import path, chdir
import click
from src.generate_web import GenerateWeb
from time import time
import logging
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    pass


@click.command(help="Generate web from repos")
@click.option("--input-db", default="db", help="Input db folder (default is db)")
@click.option(
    "--build-dir", "-o", default="build", help="build directory (default is build)"
)
@click.option(
    "--template-dir",
    "-t",
    default="templates",
    help="Template directory (default is 'templates')",
)
@click.option(
    "--static-dir", default="static", help="Static directory (default is 'static')"
)
@click.option("--verbose", default=False, is_flag=True, help="Verbose build")
@click.option(
    "--compile-tailwind",
    default=False,
    is_flag=True,
    help="Compile tailwind (requires npx + tailwindcss)",
)
def generate(
    input_db: str,
    build_dir: str,
    template_dir: str,
    static_dir: str,
    verbose: bool,
    compile_tailwind: bool,
):
    print(f"Generating web to {build_dir} directory")
    start = time()

    folder_list = [f for f in os.listdir(input_db) if "." not in f]

    def custom_sort_key(item):
        return int(item[3:])  # Extract the numeric part and convert it to an integer

    folder_list = sorted(folder_list, key=custom_sort_key)

    info: list[dict]
    refs: list[list[str]]
    transcripts: list[list[str]]

    info = [
        yaml.safe_load(open(os.path.join(input_db, folder, "index.yaml"), "r"))
        for folder in folder_list
    ]
    refs = [
        [
            open(os.path.join(input_db, folder, "refs", file), "r").read()
            for file in os.listdir(os.path.join(input_db, folder, "refs"))
        ]
        for folder in folder_list
    ]
    transcripts = [
        [
            open(os.path.join(input_db, folder, "transcripts", file), "r").read()
            for file in os.listdir(os.path.join(input_db, folder, "transcripts"))
        ]
        for folder in folder_list
    ]

    generate_web = GenerateWeb(
        info,
        refs,
        transcripts,
        build_dir,
        path.abspath(template_dir),
        static_dir,
        verbose,
        compile_tailwind,
    )

    generate_web.generate()
    print(f"Generated web to {build_dir} directory in {time() - start:.2f} seconds")


@click.command(help="Serve generated web with livereload / without livereload")
@click.option("--port", default=8000, help="Port to serve on (default is 8000)")
@click.option(
    "--host", default="localhost", help="Host to serve on (default is localhost)"
)
@click.option("--build-dir", default="build", help="build directory (default is build)")
@click.option(
    "--no-livereload",
    default=False,
    is_flag=True,
    help="Disable live reload and serve only once",
)
def serve(port: int, host: str, build_dir: str, no_livereload: bool):
    chdir(build_dir)
    if no_livereload:
        import http.server
        import socketserver

        Handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer((host, port), Handler) as httpd:
            httpd.allow_reuse_address = True
            print(f"Serving at http://{host}:{port}")
            httpd.serve_forever()
    else:
        import livereload

        server = livereload.Server()
        # watch everything in the build directory
        server.watch(".")
        print(f"Serving at http://{host}:{port}")
        server.serve(port=port, host=host)


cli.add_command(generate)
cli.add_command(serve)

if __name__ == "__main__":
    cli()
