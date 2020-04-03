## Introduction

Nagato is a Blender add-on to manage animation production tasks with [CG-wire's](https://www.cg-wire.com/) Kitsu and perform version control functions with [SVN](https://subversion.apache.org/).

## Dependences

This add-on requires two python libraries to work; CG-wire [Gazu](https://github.com/cgwire/gazu) and [Pysvn](https://pysvn.sourceforge.io/).

Gazu is a Python client for the Kitsu API. To install it, follow instructions [here](https://github.com/cgwire/gazu).

[Pysvn](https://pysvn.sourceforge.io/) is the python interface to Subversion. For installation instructions, please go [here](https://pysvn.sourceforge.io/downloads.html).


## Installation

Install it like you would any blender add-on. Click on 'Install' and locate the zip archive. 

After installation, enter the url of your kitsu server api. It should be something like 

```bash
"https://your-server-url/api"
```

The add-on interface is located on the 'Active Tool' tab (the spanner thingy) on the Properties panel.

## Usage
Kitsu is an extremely powerful tool and this add-on extends its functionality through Gazu (it's python api) to work from within Blender.

As a user, you can view your assigned tasks, set task status and comments, open working files as well as commit them to your SVN repositories.

## File trees
For the most part, the folder/directory structure was based off of the [Blender Animation Studio's pipeline](https://youtu.be/aR3yNNGK_sc?t=439) and we have provided an example file tree [here](https://github.com/eaxum/nagato/blob/master/file_tree_example.json)

You will place the JSON file in this directory on the machine your server is located...

```bash
/opt/zou/zouenv/lib/python3.6/site-packages/zou/app
```
To be able open project files from within Blender, login first, then set the project file tree by running this code from Blender's console.

```python
gazu.files.set_project_file_tree(project_id, file_tree_example)
```
You only need to do this once per project.


## Contributing
Pull requests are welcome! If you'd like to contribute to the project then simply fork the repo, work on your changes, and then submit a pull request. 

If you're unsure what to contribute, then look at the [open issues](https://github.com/eaxum/nagato/issues) for the current to-dos.
