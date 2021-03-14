git add .
unix_time=$(date +%s%3n)
git commit -m $unix_time
git push