import argparse

def convert(f_p, new_f):
    with open(f_p, 'r', encoding='utf8') as f:
        content = f.read()

    with open(new_f, 'w+', encoding='utf8') as nf:
        helper(content, nf)

def helper(content, writer):
    counter = 0
    loc = 0
    length = len(content)
    while loc < length:
        char = content[loc]
        if char == '$':
            if counter == 0:
                if content[loc+1] == '$':
                    loc += 1
                    writer.write('\n')
                writer.write('![formula](http://latex.codecogs.com/svg.latex?')
                counter += 1
            else:
                writer.write(')')
                if content[loc+1] == '$':
                    loc += 1
                    writer.write('\n')
                counter = 0
        else:
            if counter == 0 or (char != ' ' and char != '\n'):
                writer.write(char)
        loc += 1

if __name__ == "__main__":
    aparse = argparse.ArgumentParser(description='convert Latex formular into the format that Github README can show')
    aparse.add_argument('-i', required=True)
    aparse.add_argument('-o', required=True)
    command = aparse.parse_args()
    print(command.i, command.o)
    convert(command.i, command.o)