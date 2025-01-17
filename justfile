check:
    bean-check main.beancount

fava:
    fava main.beancount

identify:
    bean-identify main.import ~/Downloads

alias fmt := format
format:
    bean-format -o main.beancount main.beancount

alias cp := copy
copy:
    cp $(bean-identify main.import ~/Downloads/ | grep -B 1 "Importer:" | grep -oP '(?<=\*\*\*\* ).*') ./documents

alias mv := move
move:
    mv $(bean-identify main.import ~/Downloads/ | grep -B 1 "Importer:" | grep -oP '(?<=\*\*\*\* ).*') ./documents

extract:
    bean-extract -f main.beancount -e main.beancount main.import ~/Downloads > tmp.beancount

append:
    head -n -1 tmp.beancount  >> main.beancount
