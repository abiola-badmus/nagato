## Introduction

Nagato is a Blender add-on to manage animation production tasks with [CG-wire's](https://www.cg-wire.com/) Kitsu and perform version control functions with [SVN](https://subversion.apache.org/).

## Installation

Download the add-on from [here](https://drive.google.com/open?id=1RtmnBxgutSOtcwkHQBuVtGTUIkB6toyr).

Install it like you would any blender add-on. Click on 'Install' and locate the zip archive. If you intend to use SVN, also install the CollabnetClient in the folder. 

After installation, enter the url of your kitsu server api. It should be something like 

```bash
"https://your-server-url/api"
```

The add-on interface is located on the 'Active Tool' tab (the spanner thingy) on the Properties panel.

## Usage
Kitsu is an extremely powerful tool and this add-on extends its functionality through Gazu (it's python api) to work from within Blender.

As a user, you can view your assigned tasks, set task status and comments, open working files as well as commit them to your SVN repositories.

## Functions
Select Project: Selects an open project from the Studio for which you have tasks assigned.

Select filter: Selects a task type (Modelling, Lighting, Shading e.t.c) and filters all your current tasks by that.

Open file: opens the currently selected .blend file

Update status: Set the project status to TODO(to do), WIP(work in progress) or WFA(waiting for approval). When you Update status to 'WFA', it publishes the file automatically
There is an optional text input to leave comments.

Add file to SVN: Adds the currently opened .blend file to the project. The file has to be saved in a location within the project directory (We might remove this feature soon.)

Publish file(commit/push): The magic button. This saves your file and then uploads it to the project's central repository. The save button within blender will still work as usual but until you push this button, all the changes to the file remain on your machine and nobody else on the team has access to it.
There is an optional text input to leave comments.

Update file: this makes sure you're working on the latest version of the file.

Download project files(Checkout/Update repo): When you attempt to 'Open file', you will be required to first push this button if the files dont exist on your machine.

Consolidate maps: This consolidates all textures and images located outside of the project directory into a 'maps' folder relative to the file you're working on and then adds them to the project.

## File trees(Studio Admin)
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
Pull requests are welcome! If you'd like to contribute code to the project then simply fork the repo, work on your changes, and then submit a pull request. 

If you're unsure what to contribute, then look at the [open issues](https://github.com/eaxum/nagato/issues) for the current to-dos.
