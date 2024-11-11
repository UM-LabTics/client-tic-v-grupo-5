para ver donde esta la sd usar lsblk

Formattear SD:
sudo umount /dev/mmcblk0p1                                                  
sudo umount /dev/mmcblk0p2

Flashear SD:
sudo sdm --burn /dev/mmcblk0 --hostname raspberrypi nombreimagen.img


