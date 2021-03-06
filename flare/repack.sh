#!/bin/bash

echo $mods
echo $game_dir

abort=""
if [ -z "$mods" ]  ; then
	echo "Please define the variable mods before running this script"
	abort="yes"
fi

if [ -z "$game_dir" ] ; then
	echo "Please define the variable game_dir before running this script"
	abort="yes"
fi

if [ -n "$abort" ] ; then
	exit 1
fi

for mod in ${mods}
do
	if [ -e "${game_dir}/mods/${mod}/animations" ] ; then
		for animfile in $(find ${game_dir}/mods/${mod}/animations |grep "\.txt$")
		do
			echo $animfile
			suffixtxt=$(echo "$animfile" |tr '/' ' ' |awk '$1=$2=$3=$4=$5=$6=""; {print $0} '|tr ' ' '/')

			./spritesheetpacker.py --definition ${game_dir}/mods/${mod}/animations/${suffixtxt} --mod ${game_dir}/mods/${mod} ${spritesheetpacker_args}

			{
				cd ${game_dir}
				git commit -a -m "repack image for $suffixtxt"
				cd -
			}
		done
	else
		echo "$mod has no animations folder"
	fi
done
