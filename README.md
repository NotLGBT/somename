# Matrix-Synapse
Matrix Synapse is a server implementation of the open [Matrix](https://matrix.org) communication protocol, which enables the exchange of messages and data between users through a decentralized network. Matrix Synapse is one of the popular server solutions for creating a custom Matrix instance.

Issues addressed by Matrix Synapse:

* **Decentralization:** Matrix Synapse allows the creation of decentralized communication networks where different servers can interact with each other without the need for a centralized intermediary.
* **Privacy and Security:** The Matrix protocol provides end-to-end encryption, ensuring user privacy protection and the security of transmitted messages.
* **Open Standard:** Matrix Synapse is based on an open standard, enabling developers to create various client applications and integrations for interacting with the server.
* **Scalability:** Matrix Synapse is designed with scalability in mind, enabling it to handle a large number of users and messages.
* **Integration with other services:** Matrix Synapse supports integration with various services such as video calls, file storage, and other applications to expand communication functionality.

Matrix Synapse is a powerful tool for creating a custom communication network with a focus on security, decentralization, and extensibility.


# OIDC Provider
This service is an implementation of [OpenID Connect](https://openid.net/) protocol. OpenID Connect is an authentication and authorization protocol based on OAuth 2.0.

This service addresses the following challenges:
* **Integration with external services:** Support for the OpenID Connect protocol allows for easy integration of Matrix Synapse with service that use this protocol for authentication.
* **Unified Access Management:** Integrating Matrix Synapse with an authorization server enables a unified access management system where user rights can be centrally managed.
* **Matrix-synapse homeserver administration:** Managing homeserver users, rooms and media.

# Matrix-Synapse CLI
The [CLI tool](docs/synapse_admin_cli.md) developed for administering a Matrix Synapse offer functionalities similar to the Synapse Admin API. This tool provides a simplified method to interact with the server, perform routine administrative tasks. With CLI tool administrators can streamline server management tasks and automate repetitive operations.

The CLI tool allows administrators to:

* **User Management:** Easily create, modify, and delete user accounts, manage their permissions, and handle user-related operations seamlessly through command-line inputs.
* **Room Management:** Administer rooms, control access permissions, manage memberships, and configure room settings swiftly using intuitive command-line commands.
* **Group Management:** Create and delete Groups(communities).
* **Matrix:** execute matrix API calls.
* **Notice:** Send notifications to users from terminal.
* **Raw Requests:** Issue a custom requests to the Synapse Admin API. (in development)


# Installing and configuration
This [synapse installation](deploy/synapse_deploy.md ) document describes how to install Synapse. We recommend using Docker images or python packages.
Synapse has a variety of config options which can be used to customise its behaviour after installation. There are additional details on how to configure Synapse [here](docs/homeserver_config_documentation.md ).

Refer to the [installation guide](deploy/oidc_provider_deploy.md) for the OIDC provider service.

# Using a reverse proxy with Synapse
It is recommended to put a reverse proxy such as nginx, Apache, Caddy, HAProxy or relayd in front of Synapse. One advantage of doing so is that it means that you can expose the default https port (443) to Matrix clients without needing to run Synapse with root privileges.
