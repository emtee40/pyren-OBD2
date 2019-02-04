# Repair script for rlink2 black screen
$addr = 13

can500  # init can macro

1003

# MID 2  480x800
2E2303020D02082301E03C000004200080000A007603200D05062C006967

wait 2
# reload rlink2
1101