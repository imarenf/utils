from distutils.core import setup, Extension


def main():
    setup(name="ping",
          version="1.0.0",
          description="Python interface for the ping function, written in C",
          author="Dmitry Egorov",
          author_email="asap.illidan@gmail.com",
          ext_modules=[Extension("ping", ["ping.c"])]
          )


if __name__ == "__main__":
    main()
