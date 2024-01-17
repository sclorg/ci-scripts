**ocp-stream-generator**

The ocp generator tool generates JSON files that are consumed by the OpenShift cluster.
Adding support for generating HelmCharts is planned for the future.


For now the generator takes only one argument, which is YAML config file.
The configuration file should look like this:

```
---
- name: postgresql
  pretty_name: PostgreSQL
  sample_repo: ""
  category: database
  description: >
    Provides a PostgreSQL APP_VERSION database on DISTRO_NAME.
    For more information about using this database image,
    including OpenShift considerations,
    see https://github.com/sclorg/postgresql-container/blob/master/README.md.
  imagestream_files:
  - filename: postgresql-centos.json
    latest: "15-el9"
    distros:
      - name: CentOS Stream 8
        app_versions: [10, 12, 13, 15]

      - name: CentOS Stream 9
        app_versions: [13, 15]

  - filename: postgresql-rhel.json
    latest: "13-el7"
    distros:
      - name: RHEL 7
        app_versions: [10, 12, 13]
```
