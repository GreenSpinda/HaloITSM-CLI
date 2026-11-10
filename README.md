# HaloITSM CLI

A custom lightweight command-line for interacting with the [HaloITSM](https://www.usehalo.com/) REST API.

Current Version: **v0.1.3.261110**

Previous Version: **v0.1.2.260922**

## Overview

HaloAPI CLI provides a simple interactive terminal interface to authenticate against a Halo instance and perform common operations (`GET`, `POST`, `DELETE`) against documented endpoints (https://www.usehalo.com/swagger).

It supports:
- OAuth2 client-credentials authentication
- Automatic token refresh / expiry tracking
- Pagination handling for large result sets
- Client-side filtering
- Single-record and bulk CSV uploads
- Structure-print or raw JSON output

> **Important**: This is primarily a **Proof of Concept (PoC) / draft tool** created for testing and exploration of the HaloITSM API. While it is functional and can be used in real-world environments, this is not production-hardened software.

## Disclaimer

This tool is provided **as-is**, without any warranty of any kind, express or implied.  

By using this CLI you acknowledge and accept that:

- The author(s) accept **no liability** for any data loss, data corruption, unauthorised changes, security incidents, service disruption, or any other damage arising from the use (or misuse) of this tool.
- The tool can create, modify, and **permanently delete** records on a live HaloITSM instance.  
- You are solely responsible for:
  - Protecting your `client_id`, `client_secret`, and access tokens
  - Testing thoroughly in a non-production environment before using against live data
  - Any actions performed while the command-line interface is running
- This software is experimental in nature. Bugs, incomplete features, and unexpected behaviour may exist.

**Use at your own risk.**

## Features

- **Interactive shell** with command history-style prompt
- **GET** with optional client-side filtering, pagination, and display modes (`all`, `keys`, `raw`)
- **POST** single records or bulk upload from CSV
- **DELETE** with confirmation prompt
- **Token management** – automatic retrieval and local persistence in `config.ini`


## Requirements

- Python 3.8+
- pip `requests`

## Configuration 

The default configuration file will not contain 'client_id' and 'client_secret' options. These have been removed to inspire secure secret storage. To enable token retrieval and handling a user can add the options under the [configuration] section.

## How to utilize 

1. Download Python 3.1+
2. Run 'python3 main.py'
3. Fill in valid details to the config.ini file and save it.
4. Run 'help' in the command line for usage assistance. 
