# Repair script for rlink2 black screen
$addr = 13

can500  # init can macro

# HIGH 2 768x1024
2E2303032802131303003C000004500014001E001E040014E8002C006967

wait 2
# reload rlink2
1101