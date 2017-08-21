# Changelog
All notables changes to this project will be documented in this file.

## Unrelease
### Changed
- The API call `GET job/simple_result` now gives the pack and space group used
  to get the best percent and `q_factor`.
- The API call `GET job/simple_result` and `GET job/detailed_results` now gives
  the availability status of the final files.

## v1 04-06-2017
### Added
- Shell command to update the local contabase according to the one stored on
  the supercomputer
- Form to POST a new job
- Allow the user to make his job "confidential" (only the logged in account
  used during the creation can access the results of the job)
- Send an email when a job is complete
- Gives a page to see the compiled results of a complete job
- Provide an API to see the contabase, POST a job, see the status and results
  of a job.
