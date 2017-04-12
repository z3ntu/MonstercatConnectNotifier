#!/usr/bin/python3

def main():
    template_file = open("config.DEFAULT.py", "r")
    config = open("config.py", "w")

    template = template_file.read()
    config.write(template)

if __name__ == '__main__':
    main()
