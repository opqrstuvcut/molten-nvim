# Changelog

## [1.2.0](https://github.com/opqrstuvcut/molten-nvim/compare/v1.1.5...v1.2.0) (2023-12-02)


### Features

* add kernel interrupt and restart functions ([879272f](https://github.com/opqrstuvcut/molten-nvim/commit/879272fd47be0af67de96abeac2aae02cfce28a6))
* Cell Jumping ([#30](https://github.com/opqrstuvcut/molten-nvim/issues/30)) ([a0fcd42](https://github.com/opqrstuvcut/molten-nvim/commit/a0fcd42c0052995b09d40a5e36cda66e9ef4a12e))
* delete all outputs if `MagmaRestart!` is used ([3630306](https://github.com/opqrstuvcut/molten-nvim/commit/36303065adaeb1bdbd5a467b3235ce41ffebf480))
* export cell output to ipynb file ([#40](https://github.com/opqrstuvcut/molten-nvim/issues/40)) ([ef9cb41](https://github.com/opqrstuvcut/molten-nvim/commit/ef9cb41381926878ee832b9c96d74accbb4fabdf))
* magma_enter_output_behavior ([1f37517](https://github.com/opqrstuvcut/molten-nvim/commit/1f37517ff33cf70ffb1483eb361d8d81c70ef906))
* magma_enter_output_behavior ([fb4cb75](https://github.com/opqrstuvcut/molten-nvim/commit/fb4cb757106f894c9239077dde28d705b49b2b01))
* MagmaHideOutput command ([e750c09](https://github.com/opqrstuvcut/molten-nvim/commit/e750c091f200f99a954132a95d80dc96cae11d44))
* Output as Virtual Text ([#33](https://github.com/opqrstuvcut/molten-nvim/issues/33)) ([820463d](https://github.com/opqrstuvcut/molten-nvim/commit/820463df259d2c77d080e8106f1ad48ed4e8c7b7))
* Virtual Lines Under Output Window ([#15](https://github.com/opqrstuvcut/molten-nvim/issues/15)) ([3ae8071](https://github.com/opqrstuvcut/molten-nvim/commit/3ae807147d5b32d3adb9676397f056b07a6a0757))


### Bug Fixes

* charwise evaluateOperator was off by one ([#31](https://github.com/opqrstuvcut/molten-nvim/issues/31)) ([91ec70b](https://github.com/opqrstuvcut/molten-nvim/commit/91ec70b710bc8e1de59352b1ecfb4cdb6e786c92))
* clear interface immediately ([b91787a](https://github.com/opqrstuvcut/molten-nvim/commit/b91787a12ec3ffabdc12b6c06efdf86c41f19e49))
* duplicate virt text/virt text wrap ([#70](https://github.com/opqrstuvcut/molten-nvim/issues/70)) ([71faa0d](https://github.com/opqrstuvcut/molten-nvim/commit/71faa0d98ee6aea2167f69d9c6c67ccab1571c14))
* enter float destroying virt output ([#46](https://github.com/opqrstuvcut/molten-nvim/issues/46)) ([49ac223](https://github.com/opqrstuvcut/molten-nvim/commit/49ac223b5486eb751fadfd627c7618c3b65ad8c4))
* EvaluateArgument ([#18](https://github.com/opqrstuvcut/molten-nvim/issues/18)) ([f9c28ef](https://github.com/opqrstuvcut/molten-nvim/commit/f9c28efc13f7a262e27669b984f3839ff5c50c32))
* healthcheck on python 3.11+ ([#65](https://github.com/opqrstuvcut/molten-nvim/issues/65)) ([523d0ec](https://github.com/opqrstuvcut/molten-nvim/commit/523d0eceb3349c8deb798f52c2d827fbfdd44668))
* hide images when appropriate ([#44](https://github.com/opqrstuvcut/molten-nvim/issues/44)) ([f431035](https://github.com/opqrstuvcut/molten-nvim/commit/f4310356c6028b29da596888e0804655243f5db8))
* images being pushed down doubly by virt text ([#53](https://github.com/opqrstuvcut/molten-nvim/issues/53)) ([909f6f8](https://github.com/opqrstuvcut/molten-nvim/commit/909f6f890b6c607ee802ff8662892880dd78baec))
* images displaying when window is off screen ([225624c](https://github.com/opqrstuvcut/molten-nvim/commit/225624cc662d0050caac95586a3f54c550d79750))
* images in output windows with virt text ([#55](https://github.com/opqrstuvcut/molten-nvim/issues/55)) ([18b6b9a](https://github.com/opqrstuvcut/molten-nvim/commit/18b6b9a680cbce2b037409df79e81e7fdc10c155))
* progress bars ([a6bdb5e](https://github.com/opqrstuvcut/molten-nvim/commit/a6bdb5ed34c0cd815fac307cf83d2e3a58afcb92))
* progress bars are back to working ([c6c17eb](https://github.com/opqrstuvcut/molten-nvim/commit/c6c17ebf0ff8874749d0dda56be7f2413d29c795))
* show kernel info for ext kernels ([#29](https://github.com/opqrstuvcut/molten-nvim/issues/29)) ([29763c6](https://github.com/opqrstuvcut/molten-nvim/commit/29763c6d49eaa8d0c9c9093a88fb38db34ba4875))
* truncate output text ([#67](https://github.com/opqrstuvcut/molten-nvim/issues/67)) ([3141b93](https://github.com/opqrstuvcut/molten-nvim/commit/3141b936ee69f15f3a926b122d110b0940e152e0))
* use tmux escape codes if running in tmux ([712ad04](https://github.com/opqrstuvcut/molten-nvim/commit/712ad049051c640ae00bdd68c151dc2f0c00242c))

## [1.1.5](https://github.com/benlubas/molten-nvim/compare/v1.1.4...v1.1.5) (2023-11-30)


### Bug Fixes

* duplicate virt text/virt text wrap ([#70](https://github.com/benlubas/molten-nvim/issues/70)) ([71faa0d](https://github.com/benlubas/molten-nvim/commit/71faa0d98ee6aea2167f69d9c6c67ccab1571c14))
* healthcheck on python 3.11+ ([#65](https://github.com/benlubas/molten-nvim/issues/65)) ([523d0ec](https://github.com/benlubas/molten-nvim/commit/523d0eceb3349c8deb798f52c2d827fbfdd44668))
* truncate output text ([#67](https://github.com/benlubas/molten-nvim/issues/67)) ([3141b93](https://github.com/benlubas/molten-nvim/commit/3141b936ee69f15f3a926b122d110b0940e152e0))

## [1.1.4](https://github.com/benlubas/molten-nvim/compare/v1.1.3...v1.1.4) (2023-11-26)


### Bug Fixes

* images in output windows with virt text ([#55](https://github.com/benlubas/molten-nvim/issues/55)) ([18b6b9a](https://github.com/benlubas/molten-nvim/commit/18b6b9a680cbce2b037409df79e81e7fdc10c155))

## [1.1.3](https://github.com/benlubas/molten-nvim/compare/v1.1.2...v1.1.3) (2023-11-22)


### Bug Fixes

* images being pushed down doubly by virt text ([#53](https://github.com/benlubas/molten-nvim/issues/53)) ([909f6f8](https://github.com/benlubas/molten-nvim/commit/909f6f890b6c607ee802ff8662892880dd78baec))

## [1.1.2](https://github.com/benlubas/molten-nvim/compare/v1.1.1...v1.1.2) (2023-11-18)


### Bug Fixes

* enter float destroying virt output ([#46](https://github.com/benlubas/molten-nvim/issues/46)) ([49ac223](https://github.com/benlubas/molten-nvim/commit/49ac223b5486eb751fadfd627c7618c3b65ad8c4))

## [1.1.1](https://github.com/benlubas/molten-nvim/compare/v1.1.0...v1.1.1) (2023-11-18)


### Bug Fixes

* hide images when appropriate ([#44](https://github.com/benlubas/molten-nvim/issues/44)) ([f431035](https://github.com/benlubas/molten-nvim/commit/f4310356c6028b29da596888e0804655243f5db8))

## [1.1.0](https://github.com/benlubas/molten-nvim/compare/v1.0.0...v1.1.0) (2023-11-18)


### Features

* export cell output to ipynb file ([#40](https://github.com/benlubas/molten-nvim/issues/40)) ([ef9cb41](https://github.com/benlubas/molten-nvim/commit/ef9cb41381926878ee832b9c96d74accbb4fabdf))
* Output as Virtual Text ([#33](https://github.com/benlubas/molten-nvim/issues/33)) ([820463d](https://github.com/benlubas/molten-nvim/commit/820463df259d2c77d080e8106f1ad48ed4e8c7b7))

## 1.0.0 (2023-11-17)

### Features From Magma

- Start a kernel from a list of kernels
- Attach to already running jupyter kernel
- Send code to the Jupyter Kernel to run asynchronously
- View output in a floating window below the `cell` that you ran, including image outputs
- Cells are saved, and you can rerun them, they expand when you type, and you can pull up their
output again, and rerun them. Interact with the output in a vim buffer

### New Features (pre 1.0.0)

- Completely custom borders
- Border colors per run status
- "Cropped" window borders
- Window footer to display the number of extra lines that don't fit in the window
- configurable max window size
- Can specify no border without minimal style
- Buffers can be shared across kernels `:MoltenInit shared [kernal]`
- You can have multiple kernels running in one buffer, including the same kernel running more than
once
- Update configuration values on the fly
- Enter output can also open the output so you have one key to do both
- You can hide the output without leaving the cell
- Quitting an output window hides the output window (configurable)
- A function for running a range of lines, enabling user created code runners
- 
- Image rendering
    - Images are rendered with Image.nvim which has support for kitty and uberzug++. Much more
    consistent image rendering.
    - Configurable max image height
    - Allows for cropped images
    - CairoSVG is no longer required for rendering svg. The ImageMagic dependency of Image.nvim
    handles that for us
    - more image formats supported
- More graceful LaTeX image rendering errors
- `:MoltenInfo` command to see information about kernels
- Status line functions to see running kernels and/or initialization status


### Bug Fixes

- Kernel prompt actually works when used from the command line
- Close output command works from inside an output window
- Folding text above an output window is correctly accounted for
    - Similarly, virtual lines are correctly accounted for
- Window rendering performance: No longer redraw an open window ever, it's just updated
- Cell rendering performance: Don't redraw the cell highlights every time the window scrolls or the
cursor moves
- Run status is working again
- Save/load is working again
