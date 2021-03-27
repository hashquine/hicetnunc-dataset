class StateRecorder:
    def __init__(self, state):
        self.log = []
        self.state = state

    def __getattr__(self, attr_name):
        if not attr_name.startswith('apply_'):
            return getattr(self.state, attr_name)

        def method(*args, **kwargs):
            assert not args, 'Use keyword arguments only'
            assert 'method' not in kwargs, 'Do not pass "method" keyword argument'
            assert 'row_id' in kwargs, 'Argument row_id is required'
            assert type(kwargs['row_id']) is int and kwargs['row_id'] >= 0, 'row_id must be non-negative int'

            self.log.append({
                'method': attr_name,
                **kwargs,
            })
            method_fun = getattr(self.state, attr_name)
            return method_fun(**kwargs)

        return method


class ReachedLogReplayEndException(Exception):
    pass


class StateReplayer:
    def __init__(self, log, state):
        self.log = log
        self.state = state
        self.validate_log()
        self.reset()

    def validate_log(self):
        prev_row_id = -1
        for entry in self.log:
            cur_row_id = entry['row_id']
            assert type(cur_row_id) is int
            assert prev_row_id < cur_row_id
            prev_row_id = cur_row_id

    def reset(self):
        self.state.reset()
        self.log_entry_no = 0

    def step_forward(self):
        if self.log_entry_no >= len(self.log):
            raise ReachedLogReplayEndException()
        log_entry = self.log[self.log_entry_no]
        method_name = log_entry['method']
        method_fun = getattr(self.state, method_name)
        kwargs = dict(log_entry)
        del kwargs['method']
        method_fun(**kwargs)
        self.log_entry_no += 1

    def replay_to_end(self):
        while not self.reached_end():
            self.step_forward()
        assert self.log_entry_no == len(self.log)

    def reached_end(self):
        return self.log_entry_no >= len(self.log)

    def applied_log_row_id(self):
        if self.log_entry_no == 0:
            return -1
        applied_log_entry = self.log[self.log_entry_no - 1]
        return applied_log_entry['row_id']

    def next_log_row_id(self):
        if self.log_entry_no >= len(self.log):
            raise ReachedLogReplayEndException()
        next_log_entry = self.log[self.log_entry_no]
        return next_log_entry['row_id']

    def replay_to_before_row_id(self, row_id):
        assert row_id >= 0
        if self.applied_log_row_id() >= row_id:
            self.reset()
        while self.next_log_row_id() < row_id:
            self.step_forward()
        assert self.applied_log_row_id() < row_id
        assert self.next_log_row_id() >= row_id

    def replay_to_after_row_id(self, row_id):
        self.replay_to_before_row_id(row_id)
        if self.next_log_row_id() == row_id:
            self.step_forward()
        assert self.applied_log_row_id() <= row_id
        assert self.next_log_row_id() > row_id

