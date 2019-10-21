WEB_REPO="../../hugo-site/public"

python3 update_fm_courses.py
mv fme-courses-github.js ${WEB_REPO}/courses/data

cd ${WEB_REPO}
git pull
git commit -am "Update courses list."
git push
