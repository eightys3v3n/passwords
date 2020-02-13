from pathlib import Path
from sys import argv
from enum import Enum
import progressbar
import os


def list_files(path, recursive=True):
    files = []
    assert isinstance(path, Path)

    for p in path.iterdir():
        if p.is_file() and not p.is_symlink():
            files.append(p)
        elif recursive and p.is_dir():
            files.extend(list_files(p))
    return files


def filter_files(files):
    def valid_file(path):
        if path.suffix not in FileExtensions: return False
        for f in OutputFiles:
            if f.exists():
                if path.samefile(f): return False
        if path.name.startswith("."): return False
        return True
    new_files = filter(valid_file, files)
    return list(new_files)


def read_lines(file):
    lines = []
    print("Reading file '{}'".format(file))
    with open(file, 'rb') as f:
        lines = [l.strip() for l in f]
    lines = [l.decode("utf-8", errors="ignore") for l in lines]
    lines = [line.strip() for line in lines]
    return lines


def read_files(files):
    words = []
    print("Reading {} files.".format(len(files)))
    for f in files:
        words.extend(read_lines(f))
    return words


def deduplicate(stuffs):
    unique_stuff = set()
    for stuff in stuffs:
        unique_stuff.add(stuff)
    return unique_stuff


def write_words(path, words):
    print("Writing words into '{}'".format(path))
    with open(path, 'w') as f:
        for w in words:
            f.write(w+"\n")


def filter_symbols(words):
    return filter(lambda x:x.isalnum(), words)


def only_symbols(words):
    return filter(lambda x:not x.isalnum(), words)


def combined_files(root):
    files = list_files(root)
    #print("Found {} files.".format(len(files)))

    # remove invalid extensions and files that this script outputs.
    files = filter_files(files)
    #print("Found {} txt files.".format(len(files)))

    words = read_files(files)
    #print("Found {} words.".format(len(words)))
    
    return words
 

def unique_combined(words):
    unique_words = deduplicate(words)
    #print("Found {} unique words.".format(len(unique_words)))
    #print("{:2.2f}% of words were duplicates.".format(len(unique_words)/len(words)*100))

    return unique_words


def must_have_symbols(words):
    symbols_only = only_symbols(words)
    #print("{:2.2f}% have symbols.".format(len(symbols_only)/len(words)*100))
    
    return symbols_only


def without_symbols(words):
    no_symbols = filter_symbols(words)
    #print("{:2.2f}% don't have symbols.".format(len(no_symbols)/len(words)*100))
    
    return no_symbols


def within_lengths(words, *, min_len=0, max_len=None):
    within_range = []
    if max_len is not None:
        within_range = filter(lambda x:len(x) <= max_len and len(x) >= min_len, words)
    else:
        within_range = filter(lambda x:len(x) >= min_len, words)
    #print("Found {} words within range.".format(len(within_range)))
    #print("{:2.2f}% of words were in length range {}-{}.".format(len(within_range)/len(words)*100, min_len, max_len))
    
    return within_range


def remove_2nd_from_1st(words, remove_words):
    unchecked_words = words
    removed = 0
    for rw in remove_words:
        while rw in unchecked_words:
            unchecked_words.remove(rw)
            removed += 1
    print("Removed {} words.".format(removed))
    return unchecked_words


# Remove stuff that doesn't contain a dictionary word
# Do everything in iterators instead of reading into RAM


def main():
    global OutputFiles, FileExtensions
    FileExtensions = ['.txt', '.lst'] # File extensions to scan.
    output_extension = ".lst"
    OutputFiles = [ # these files are Not scanned when reading password lists.
        Path(__file__),
        Path('lists/unique_combined' + output_extension),
        Path('lists/unique_le_15' + output_extension),
        Path('lists/unchecked' + output_extension),
    ]

    # Read all passwords into memory.
    print("Reading all passwords...")
    words = combined_files(Path('lists'))
    
    # Writes the unique words from all files into a combined password list.
    print("Finding unique passwords...")
    unique_words = unique_combined(words)
    del words
    write_words(OutputFiles[1], unique_words)

    # Saves passwords for Microsoft Office 2013 (less than or equal to 15 in length).
    print("Removing passwords longer than 15...")
    less_than_15 = within_lengths(unique_words, max_len=15)
    del unique_words
    write_words(OutputFiles[2], less_than_15)

    print("Removing checked passwords...")
    checked = read_lines("unique_combined.lst")
    unchecked_words = remove_2nd_from_1st(less_than_15, checked)
    write_words(OutputFiles[3], unchecked_words)


if __name__ == '__main__':
    main()
