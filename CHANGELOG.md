# Changelog
All notables changes to this project will be documented in this file.

## Unrelease	
### General
- If an e-mail address is available (given in the submission form
  or given in the "email_address" field of the `POST job` request),
  a notification email is sent when the job has been submitted (and
  not only when the job is complete, as done previously).
- ContaMiner now accepts PDB files as custom contaminants.
	
### API
- To simplify the structure parsing, a "monomer" value in
  ContaBase.Contaminant.Pack.structure is now written "1-mer". (Affects
  `GET contabase`, `GET detailed_categories`, `GET detailed_category`,
  `GET detailed_contaminants`, `GET detailed_contaminant`)
- In order to fix some inacuracies, the value "domain" for
  ContaBase.Contaminant.Pack.Structure has been removed, and replaced by the
  already existing "domains". (Affects `GET contabase`,
  `GET detailed_categories`, `GET detailed_category`, `GET detailed_contaminants`,
  `GET detailed_contaminant`)
- Job.status can now have the value "New" if the job has not yet been
  submitted to the cluster. (Affects `GET job/status`)
- Job.Task.status cannot be "Cancelled" anymore, as ContaMiner does not
  cancel the other tasks if a positive result is already found. (Affects
  `GET job/status`)
- Job.Task.status cannot be "Aborted" anymore. It has been replaced by
  "Complete", with percent and q_factor attributes set to 0. (Affects
  `GET job/status`)
- The API call `GET job/result` now gives the pack and space group used
  to get the best percent and `q_factor`.
- The API call `GET job/result` now gives a message if a positive result
  is found for a contaminant without a known structure.
- The API calls `GET job/result` and `GET job/detailed_results` now give
  the availability status of the final files.
- The API calls `GET job/result` and `GET job/detailed_result` give an error
  only if the job does not exist or is in error. If no result is available,
  return empty result.
- If a session cookie with a valid logged in session is sent with in request
  to the API, the access to a confidential job owned by the logged in user is
  now possible. (However, no way to log in through the API is currently
  available.)
	
### User interface
- The results page is now available as soon as the job is running (even if
  not complete).
- The results are automatically updated on the result page.
- Various design updates.
- (Bugfix): A bug was preventing some jobs to be submitted in confidential
  mode.

### Documentation
- The status available in `GET job/simple_result` and `GET job/detailed_result`
  first letter is now upper case. (The implementation was already uppercase,
  but the documentation was not updated.)
- Update to reflect the last API modifications (See API section).

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
