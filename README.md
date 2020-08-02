## Introduction

Nagato is a Blender add-on to manage animation production tasks with [CG-wire's](https://www.cg-wire.com/) Kitsu and perform version control functions with [SVN](https://subversion.apache.org/).

## Dependencies

Nagato is only an extension of [CG-Wire's Kitsu](https://www.cg-wire.com/). To get this to work in Blender, you need to have a Kitsu account (you can also host it yourself) as well as an SVN repository where you project files are stored.

## Installation

Download the add-on from [here](https://gumroad.com/l/xVnjW).

Install it like you would any blender add-on. Click on 'Install' and locate the zip archive.

After installation, enter the url of your kitsu server api. It should be something like 

```bash
"https://your-server-url/api"
```

The add-on interface is located on the 'Active Tool' tab (the spanner thingy) on the Properties panel.

## Usage
Kitsu is an extremely powerful tool and this add-on extends its functionality to work from within Blender.

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

Update file: Update the currently open file to the most recent revision.

Update all files: Update the entire project repository.

Reset file: Revert currently open file to the most recent revision.

Resolve conflict: Resolve any conflicts between project files.

Clean up: Clean up and break file locks.

Download project files(Checkout/Update repository): When you attempt to 'Open file', you will be required to first push this button if the files dont exist on your machine.

Consolidate maps: This consolidates all textures and images located outside of the project directory into a 'maps' folder relative to the file you're working on and then adds them to the project.

## Asset Browser
Link asset/Link selected assets: Link assets into currently open file.

Append asset/Append selected assets: Append assets into currently open file.

## File trees(Studio Admin)
For the most part, the folder/directory structure was based off of the [Blender Animation Studio's pipeline](https://youtu.be/aR3yNNGK_sc?t=439) and we have provided an example file tree [here](https://github.com/eaxum/nagato/blob/master/file_tree_example.json)

## Contributing
Pull requests are welcome! If you'd like to contribute code to the project then simply fork the repo, work on your changes, and then submit a pull request. 

If you're unsure what to contribute, then look at the [open issues](https://github.com/eaxum/nagato/issues) for the current to-dos.
