#!/bin/bash

# The script updates image description into Quay.io
set -ex

TARGET_OS=$1
gituser=$2
gitproject=$3

function post_data() {
  local name=$1
  local description=$2
  echo -n '{"description":"' > data.json
  echo -n $description >> data.json
  echo -n '"}' >> data.json

  curl -d @data.json -X PUT -k -H "Authorization: Bearer $QUAY_OAUTH_TOKEN" \
       -H 'Content-Type: application/json' \
       "https://quay.io/api/v1/repository/${TARGET_OS}/${name}"
}

for version in $(grep "VERSIONS = " Makefile | sed "s|VERSIONS = ||"); do
  for image in $(make tag TARGET=${TARGET_OS} VERSIONS=${version} | grep -- '-> Tagging image' | cut -d' ' -f 6 | sed "s/'//g"); do
    echo "Updating summary for ${image}"
    description=$(docker inspect --format='{{.Config.Labels.description}}' ${image} || "")
    if [ ${#description} -gt 100 ] ; then
      description="${description:0:96}..."
    fi
    name=${image##*/}
    echo "Update Quay.io with description and link to README.md on GitHub"
    echo "Check if generated branch exist"
    generated_branch=""
    if git ls-remote --exit-code origin generated; then
      generated_branch="blob/generated/"
    fi

    README_MD="${version}/README.md"
    if [ -L "${README_MD}" ] ; then
      # In case e.g. in redis-container
      # 5/README.md -> root/usr/share/container-scripts/redis/README.md
      # Then we have to update link to 5/root/usr/share/container-scripts/redis/README.md
      readme_file=$(readlink "${README_MD}")
      if [[ x"${generated_branch}" == "x" ]]; then
        generated_branch="blob/master/"
      fi
      description="${description}.<br>Learn more <a href=\\\"https://github.com/${gituser}/${gitproject}/${generated_branch}${version}/${readme_file}\\\">https://github.com/${gituser}/${gitproject}/${generated_branch}${version}/${REAL_FILE}</a>"
      post_data "${name%:*}" "${description}"
    elif [ -f "${README_MD}" ]; then
      description="${description}.<br>Learn more <a href=\\\"https://github.com/${gituser}/${gitproject}/${generated_branch}${README_MD}\\\">https://github.com/${gituser}/${gitproject}/${generated_branch}${README_MD}</a>"
      post_data "${name%:*}" "${description}"
    fi
  done
done
