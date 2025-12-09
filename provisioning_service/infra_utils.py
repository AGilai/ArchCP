import sys

def set_tab_title(title: str):
    """Sets the iTerm2 Tab Title."""
    # Code 1 sets the Tab Title (Icon Name)
    sys.stdout.write(f"\x1b]1;{title}\x07")
    # Code 2 sets the Window Title (just in case)
    sys.stdout.write(f"\x1b]2;{title}\x07")
    sys.stdout.flush()