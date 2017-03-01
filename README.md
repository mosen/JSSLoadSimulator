# JSSLoadSimulator

## Requirements



## Usage

    $ jssLoadSimulator -n <number of new computers> \
         -u <number of times to update> \
         -d <time in seconds delay> \
         -o <option for update 'u' or check in 'c'>


## Preferences

Preferences are located at `~/Library/Preferences/com.jamfsoftware.jssloadsimulator.plist`

*NOTE:* Only XML Formatted plist is supported for now.

Supported Keys

| Key      | Description |
| -------- | ----------- |
| jss_host | Hostname of the JSS |
| jss_port | Port the JSS is listening on |
| jss_path | Path to the JSS instance (if any) |

You can set these using `defaults` eg.

    $ defaults write com.jamfsoftware.jssloadsimulator jss_host localhost
    $ defaults write com.jamfsoftware.jssloadsimulator jss_port 8443
    $ defaults write com.jamfsoftware.jssloadsimulator jss_path /
    
Then, convert back to xml:

    $ plutil -convert xml1 ~/Library/Preferences/com.jamfsoftware.jssloadsimulator.plist

