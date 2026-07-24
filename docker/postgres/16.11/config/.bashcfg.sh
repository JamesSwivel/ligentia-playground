
##################### history ##############################
#Enlarge the history.. change the value by adding a 0 at the end
HISTSIZE=10000
HISTFILESIZE=20000

# Enable vi to edit command history, and map HOME/END key
set -o vi
bind -m vi-insert '"\e[1~": beginning-of-line'
bind -m vi-insert '"\e[4~": end-of-line'

##################### prompt ##############################
# color prompt (long: username & hostname & directory)
# root has red highlight
if [ "$(id -un)" != "root" ]; then
    export PS1="\[\033[38;5;11m\]\u\[$(tput sgr0)\]\[\033[38;5;15m\]@\[$(tput bold)\]\[$(tput sgr0)\]\[\033[38;5;33m\]\h\[$(tput sgr0)\]\[$(tput sgr0)\]\[\033[38;5;15m\]:\[$(tput sgr0)\]\[\033[38;5;6m\][\w]:\[$(tput sgr0)\]\[\033[38;5;15m\] \[$(tput sgr0)\]"
else
    export PS1="\[\033[38;5;161m\]\u\[$(tput sgr0)\]\[\033[38;5;15m\]@\[$(tput sgr0)\]\[\033[38;5;33m\]\h\[$(tput sgr0)\]\[\033[38;5;15m\]:\[$(tput sgr0)\]\[\033[38;5;10m\][\w]\[$(tput sgr0)\]\[\033[38;5;15m\]: \[$(tput sgr0)\]"
fi


#color prompt (directory only and max depth of 3)
#export PS1="\[$(tput sgr0)\]\[\033[38;5;6m\][\w]:\[$(tput sgr0)\]\[\033[38;5;15m\] \[$(tput sgr0)\]"
export PROMPT_DIRTRIM=4

##################### alias ##############################
alias update="sudo apt-get update; sudo apt-get -y upgrade"
alias dmesg="dmesg -T"
alias ll="ls -la"

##################### Additional PATH ##############################
## Add PATH: local bin
PATH_To_ADD=${HOME}/.local/bin
## Export PATH
[[ -z $TMUX ]] && export PATH=$PATH_To_ADD:$PATH

##################### Additional export ##############################
[[ -z $TMUX ]] && [[ -d /usr/share/dotnet ]] && export DOTNET_ROOT=/usr/share/dotnet

##################### terminal ##############################
# fix strange character
export TERM=xterm
export NCURSES_NO_UTF8_ACS=1
export LANG="C.UTF-8"

## Instruct xWin app to connect via display number 10, i.e. port 6010
#export DISPLAY=:10.0

# undefine CTRL-s/CTRL-q to stop/resume
stty stop undef
stty start undef
stty -ixon -ixoff
