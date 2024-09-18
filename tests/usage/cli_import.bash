for deployment in "east" "west" "north"; do
  grafanarmadillo --cfg "$grafanarmadillo_cfg" --api-version "${GRAFANARMADILLO_API_VERSION}" dashboard import --mapping 'file://mapping.json' --src ./my_system.json --dst "/$deployment/my_system" --env-grafana "$deployment" --env-template template
done