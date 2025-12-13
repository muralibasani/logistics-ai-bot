create database db_logistics_chatbot;
create user dbadmin with encrypted password 'dbadmin321';
grant select on all tables in schema public TO dbadmin;
grant update on all tables in schema public TO dbadmin;
grant insert on all tables in schema public TO dbadmin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO dbadmin;

grant all privileges on database db_logistics_chatbot to dbadmin;