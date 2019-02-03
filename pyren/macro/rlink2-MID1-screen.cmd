# Repair script for rlink2 black screen
$addr = 13

can500  # init can macro

# MID 1  480x800
2E230301F404080801E03C0000039D000A0005006E03200AD7022C006967

wait 2
# reload rlink2
1101