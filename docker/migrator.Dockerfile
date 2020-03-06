FROM webdevops/liquibase:postgres

USER root

WORKDIR /liquibase

COPY docker/migrator.entripoint.sh ./migrator.sh
RUN chmod +x migrator.sh

COPY jwt-app/src/changelog .

ENTRYPOINT ["./migrator.sh"]

CMD ["update"]
