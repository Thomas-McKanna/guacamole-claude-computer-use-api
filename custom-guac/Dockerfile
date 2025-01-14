# Use the existing guacamole/guacamole image as the base
FROM guacamole/guacamole:1.5.5

# Enable setting properties from environment variables
USER root
RUN echo "enable-environment-properties: true" >> /opt/guacamole/guacamole.properties 
USER guacamole

# This secret was generated using the following command:
# echo -n "ThisIsATest" | md5sum
ENV JSON_SECRET_KEY=4c0b569e4c96df157eee1b65dd0e4d41

ENV GUACAMOLE_HOME=/opt/guacamole
