# x-cli-py - A simple CLI tool for x.com

This is a web scraping based tool for x.com.
You don't need API key or any other credentials, which is cheap and easy to use.
Although, please use it at your own risk as it may violate the terms of x.com.

## install

```sh
# from source
poetry install

# from pypi
pip install x-cli-py
```

## usage

Please refer to the help message for usage details, but here is a simple example.

```sh
# setting up
# the chrome window will open, and you need to login to x.com by yourself for the first time.
# if you want to change the account, you have to run setup again.
xcli setup

# get the latest timeline.
# the default setting will get the Following timeline.
xcli tl
xcli tl --tab 1

# post some text.
# your default text editor (`echo $EDITOR`) will open.
xcli post

# if you forget the account you are using, you can check it.
xcli whoami

# you can refer to the help message
xcli --help
```

## contribution

Please feel free to open an issue or pull request.
[x-cli-py repository](https://github.com/tuesdayjz/x-cli-py)
